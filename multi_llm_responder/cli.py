from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_CONFIG_PATH = Path("models.example.json")
DEFAULT_TIMEOUT_SECONDS = 120


class ConfigError(Exception):
    """Raised when the CLI configuration is invalid."""


@dataclass(slots=True)
class ModelConfig:
    name: str
    backend: str
    model: str
    base_url: str
    system_prompt: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelConfig":
        required_fields = ("name", "backend", "model", "base_url")
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            missing_fields = ", ".join(missing)
            raise ConfigError(f"Fehlende Pflichtfelder in Modellkonfiguration: {missing_fields}")

        backend = str(data["backend"]).strip().lower()
        if backend not in {"ollama", "openai"}:
            raise ConfigError(
                f"Unbekanntes Backend '{data['backend']}'. Erlaubt sind 'ollama' und 'openai'."
            )

        headers = data.get("headers", {})
        if not isinstance(headers, dict):
            raise ConfigError(f"'headers' muss ein Objekt sein: {data['name']}")

        return cls(
            name=str(data["name"]).strip(),
            backend=backend,
            model=str(data["model"]).strip(),
            base_url=str(data["base_url"]).rstrip("/"),
            system_prompt=data.get("system_prompt"),
            api_key=data.get("api_key"),
            api_key_env=data.get("api_key_env"),
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=int(data["max_tokens"]) if data.get("max_tokens") is not None else None,
            headers={str(key): str(value) for key, value in headers.items()},
        )

    def resolved_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            return os.environ.get(self.api_key_env)
        return None


@dataclass(slots=True)
class ModelResponse:
    name: str
    backend: str
    model: str
    ok: bool
    content: str = ""
    error: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m multi_llm_responder",
        description="Fragt mehrere lokale oder selbst gehostete LLM-Endpunkte parallel ab.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Benutzereingabe. Wenn leer, wird aus stdin gelesen.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Pfad zur JSON-Konfiguration. Standard: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Überschreibt den System-Prompt für alle Modelle.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Timeout pro Anfrage in Sekunden. Standard: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Gibt die Ergebnisse als JSON aus.",
    )
    return parser


def load_prompt(prompt_arg: str | None) -> str:
    if prompt_arg and prompt_arg.strip():
        return prompt_arg.strip()

    if not sys.stdin.isatty():
        stdin_prompt = sys.stdin.read().strip()
        if stdin_prompt:
            return stdin_prompt

    raise ConfigError("Kein Prompt angegeben. Nutze ein Argument oder stdin.")


def load_models(path: Path) -> list[ModelConfig]:
    if not path.exists():
        raise ConfigError(
            f"Konfigurationsdatei nicht gefunden: {path}. "
            "Lege eine JSON-Datei an oder starte mit models.example.json."
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Ungültiges JSON in {path}: {exc}") from exc

    if not isinstance(raw, list) or not raw:
        raise ConfigError("Die Konfiguration muss ein nicht-leeres JSON-Array sein.")

    return [ModelConfig.from_dict(entry) for entry in raw]


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **headers,
    }
    req = request.Request(url=url, data=body, headers=request_headers, method="POST")

    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Verbindung fehlgeschlagen: {exc.reason}") from exc

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Antwort ist kein valides JSON: {response_body[:300]}") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Antwortformat ist ungültig.")
    return parsed


def query_openai_backend(model: ModelConfig, prompt: str, system_prompt: str | None, timeout: int) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = dict(model.headers)
    api_key = model.resolved_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model.model,
        "messages": messages,
        "temperature": model.temperature,
    }
    if model.max_tokens is not None:
        payload["max_tokens"] = model.max_tokens

    data = post_json(f"{model.base_url}/chat/completions", payload, headers, timeout)

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"Keine 'choices' in Antwort gefunden: {data}")

    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                text_parts.append(part["text"])
        if text_parts:
            return "\n".join(text_parts).strip()

    raise RuntimeError(f"Kein Textinhalt in Antwort gefunden: {data}")


def query_ollama_backend(model: ModelConfig, prompt: str, system_prompt: str | None, timeout: int) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model.model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": model.temperature},
    }
    if model.max_tokens is not None:
        payload["options"]["num_predict"] = model.max_tokens

    data = post_json(f"{model.base_url}/api/chat", payload, model.headers, timeout)

    message = data.get("message")
    if not isinstance(message, dict):
        raise RuntimeError(f"Kein 'message'-Objekt in Antwort gefunden: {data}")

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    raise RuntimeError(f"Kein Textinhalt in Antwort gefunden: {data}")


def query_model(model: ModelConfig, prompt: str, system_override: str | None, timeout: int) -> ModelResponse:
    system_prompt = system_override if system_override is not None else model.system_prompt

    try:
        if model.backend == "openai":
            content = query_openai_backend(model, prompt, system_prompt, timeout)
        else:
            content = query_ollama_backend(model, prompt, system_prompt, timeout)
        return ModelResponse(
            name=model.name,
            backend=model.backend,
            model=model.model,
            ok=True,
            content=content,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should show per-model errors.
        error_message = format_backend_error(model, exc)
        return ModelResponse(
            name=model.name,
            backend=model.backend,
            model=model.model,
            ok=False,
            error=error_message,
        )


def format_backend_error(model: ModelConfig, exc: Exception) -> str:
    raw_error = str(exc)

    if "Connection refused" in raw_error or "[Errno 111]" in raw_error:
        if model.backend == "ollama":
            return (
                f"{raw_error}. Ollama ist auf {model.base_url} nicht erreichbar. "
                "Starte `ollama serve` oder passe `base_url` in der Konfiguration an."
            )
        return (
            f"{raw_error}. Der OpenAI-kompatible Server ist auf {model.base_url} nicht erreichbar. "
            "Starte den Server oder passe `base_url` an."
        )

    if "timed out" in raw_error.lower():
        return (
            f"{raw_error}. Der Server unter {model.base_url} hat nicht rechtzeitig geantwortet. "
            "Erhoehe `--timeout` oder pruefe die Serverlast."
        )

    if "Operation not permitted" in raw_error:
        return (
            f"{raw_error}. In dieser Umgebung sind lokale HTTP-Verbindungen blockiert oder nicht erlaubt."
        )

    return raw_error


def format_text_output(prompt: str, results: list[ModelResponse]) -> str:
    chunks = [f"Prompt: {prompt}"]
    for result in results:
        header = f"[{result.name}] backend={result.backend} model={result.model}"
        if result.ok:
            body = result.content
        else:
            body = f"FEHLER: {result.error}"
        chunks.append(f"{header}\n{textwrap.indent(body, '  ')}")
    return "\n\n".join(chunks)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        prompt = load_prompt(args.prompt)
        models = load_models(args.config)
    except ConfigError as exc:
        print(f"Konfigurationsfehler: {exc}", file=sys.stderr)
        return 2

    results: list[ModelResponse] = []
    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        future_map = {
            pool.submit(query_model, model, prompt, args.system, args.timeout): model.name for model in models
        }
        for future in as_completed(future_map):
            results.append(future.result())

    results.sort(key=lambda item: item.name.lower())

    if args.json:
        json_output = {
            "prompt": prompt,
            "results": [
                {
                    "name": result.name,
                    "backend": result.backend,
                    "model": result.model,
                    "ok": result.ok,
                    "content": result.content,
                    "error": result.error,
                }
                for result in results
            ],
        }
        print(json.dumps(json_output, ensure_ascii=False, indent=2))
    else:
        print(format_text_output(prompt, results))

    return 0
