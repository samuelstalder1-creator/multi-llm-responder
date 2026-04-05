# multi-llm-responder

Kleines `uv`-basiertes Python-CLI, das einen Prompt annimmt und mehrere selbst gehostete LLMs parallel abfragt.

Die Beispielkonfiguration ist auf kleine lokale Modelle fuer ca. `48 GB` GPU-VRAM ausgelegt.

Unterstuetzte Backends:

- `ollama` fuer lokale Modelle wie Qwen, Llama, Gemma
- `openai` fuer OpenAI-kompatible Server wie `vLLM`, `LM Studio`, `text-generation-webui` oder eigene Proxys

## Setup

```bash
uv run python -m multi_llm_responder --config models.example.json "Hallo Welt"
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
    "name": "qwen-fast",
    "backend": "ollama",
    "model": "qwen2.5:3b",
    "base_url": "http://127.0.0.1:11434"
  },
  {
    "name": "qwen-balanced",
    "backend": "ollama",
    "model": "qwen2.5:7b",
    "base_url": "http://127.0.0.1:11434"
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

## Empfehlung Fuer 48 GB VRAM

Fuer reinen Inference-Betrieb mit kleinen Modellen wuerde ich bei `3B` bis `8B` bleiben. Damit bekommst du mehrere Modelle parallel auf die GPU, statt ein einzelnes groesseres Modell auszureizen.

Voreinstellung in [models.example.json](models.example.json):

- `qwen2.5:3b` fuer schnelle allgemeine Antworten
- `qwen2.5:7b` als guter Allrounder
- `qwen2.5-coder:7b` fuer Coding
- `gemma3:4b` fuer kompaktes multilinguales Modell
- `llama3.1:8b` als zweiter Allrounder

Diese Modellgroessen liegen laut den aktuellen Ollama-Library-Seiten vom `5. April 2026` grob bei:

- `qwen2.5:3b`: ca. `1.9 GB`
- `qwen2.5:7b`: ca. `4.7 GB`
- `qwen2.5-coder:7b`: ca. `4.7 GB`
- `gemma3:4b`: ca. `3.3 GB`
- `llama3.1:8b`: ca. `4.9 GB`

Das ergibt als grobe Summe nur rund `19.5 GB` Modellgewicht. Der Rest von `48 GB` bleibt fuer KV-Cache, Parallelanfragen und Runtime-Overhead. Das ist eine Inferenz aus den offiziellen Modellgroessen; der echte Bedarf haengt von Quantisierung, Kontextlaenge und Anzahl gleichzeitiger Requests ab.

Modelle laden:

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull gemma3:4b
ollama pull llama3.1:8b
```

Wenn du lieber nur drei Modelle parallel fahren willst, wuerde ich diese Auswahl nehmen:

- `qwen2.5:7b`
- `qwen2.5-coder:7b`
- `gemma3:4b` oder `llama3.1:8b`

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

Falls du mit "Gemini" eigentlich Google meinst: selbst hostbar ist in der Regel `Gemma`, nicht `Gemini`. Echtes Gemini ist normalerweise kein selbst gehostetes Modell. Falls du einen Gemini-kompatiblen Proxy oder einen OpenAI-kompatiblen Wrapper betreibst, kannst du ihn ueber das `openai`-Backend anbinden.
