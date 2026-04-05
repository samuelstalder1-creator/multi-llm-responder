# multi-llm-responder

Kleines `uv`-basiertes Python-CLI, das einen Prompt annimmt und mehrere selbst gehostete LLMs parallel abfragt.

Unterstuetzte Backends:

- `ollama` fuer lokale Modelle wie Qwen, Llama, Gemma
- `openai` fuer OpenAI-kompatible Server wie `vLLM`, `LM Studio`, `text-generation-webui` oder eigene Proxys

## Setup

```bash
uv run python -m multi_llm_responder "Hallo Welt"
```

Alternativ:

```bash
python -m multi_llm_responder "Hallo Welt"
```

## Konfiguration

Passe `models.example.json` an oder lege eine eigene Datei an:

```json
[
  {
    "name": "qwen-local",
    "backend": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://127.0.0.1:11434"
  },
  {
    "name": "gemma-vllm",
    "backend": "openai",
    "model": "google/gemma-3-12b",
    "base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY"
  }
]
```

Wichtige Felder:

- `name`: frei waehlbarer Anzeigename
- `backend`: `ollama` oder `openai`
- `model`: Modellname auf dem jeweiligen Server
- `base_url`: Basis-URL des Servers
- `system_prompt`: optional
- `api_key`: optional fuer OpenAI-kompatible Server
- `api_key_env`: optional, falls der API-Key aus einer Umgebungsvariable gelesen werden soll
- `temperature`: optional, Standard `0.7`
- `max_tokens`: optional
- `headers`: optional fuer zusaetzliche HTTP-Header

## Beispiele

Prompt direkt als Argument:

```bash
uv run python -m multi_llm_responder "Erklaere Quantencomputing in zwei Saetzen."
```

Prompt ueber `stdin`:

```bash
echo "Schreibe einen kurzen Werbetext fuer ein Fahrrad." | uv run python -m multi_llm_responder
```

Eigene Konfigurationsdatei:

```bash
uv run python -m multi_llm_responder --config my-models.json "Was ist Rust?"
```

JSON-Ausgabe:

```bash
uv run python -m multi_llm_responder --json "Vergleiche Python und Go."
```

## Hinweis zu Gemini

Echtes Gemini ist normalerweise kein selbst gehostetes Modell. Falls du einen Gemini-kompatiblen Proxy oder einen OpenAI-kompatiblen Wrapper betreibst, kannst du ihn ueber das `openai`-Backend anbinden.
