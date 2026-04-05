# multi-llm-responder

Kleines `uv`-basiertes Python-CLI, das einen Prompt annimmt und mehrere selbst gehostete LLMs parallel abfragt.

Die Beispielkonfiguration deckt jetzt kleine, mittlere und groessere lokale Modelle fuer ca. `48 GB` GPU-VRAM ab.

Unterstuetzte Backends:

- `ollama` fuer lokale Modelle wie Qwen, Llama, Gemma
- `openai` fuer OpenAI-kompatible Server wie `vLLM`, `LM Studio`, `text-generation-webui` oder eigene Proxys

## Setup

Ollama installieren und starten:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

In einem zweiten Terminal die aktivierten Standardmodelle laden:

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:8b
ollama pull command-r7b:7b
ollama pull gemma3:4b
ollama pull llama3.1:8b
```

Pruefen, ob die Modelle vorhanden sind:

```bash
ollama list
```

Danach das CLI starten:

```bash
uv run python -m multi_llm_responder --config models.example.json "Hallo Welt"
```

Alternativ:

```bash
python -m multi_llm_responder "Hallo Welt"
```

Vor dem ersten Aufruf muss Ollama laufen:

```bash
ollama serve
```

Wenn `ollama list` leer ist oder "no models loaded" anzeigt, fehlen die lokalen Modelle noch. Fuehre dann die `ollama pull ...` Befehle von oben aus.

Alle Modelle liegen in einer Datei: `models.example.json`. Schwere Modelle sind dort per `enabled: false` standardmaessig deaktiviert.

## Konfiguration

Passe `models.example.json` an oder lege eine eigene Datei an:

```json
[
  {
    "name": "qwen-fast",
    "backend": "ollama",
    "model": "qwen2.5:3b",
    "base_url": "http://127.0.0.1:11434",
    "enabled": true
  },
  {
    "name": "deepseek-reasoning",
    "backend": "ollama",
    "model": "deepseek-r1:8b",
    "base_url": "http://127.0.0.1:11434",
    "enabled": true
  }
]
```

Wichtige Felder:

- `name`: frei waehlbarer Anzeigename
- `backend`: `ollama` oder `openai`
- `model`: Modellname auf dem jeweiligen Server
- `base_url`: Basis-URL des Servers
- `enabled`: optional, Standard `true`; deaktivierte Modelle werden ignoriert
- `system_prompt`: optional; standardmaessig wird keiner gesetzt
- `api_key`: optional fuer OpenAI-kompatible Server
- `api_key_env`: optional, falls der API-Key aus einer Umgebungsvariable gelesen werden soll
- `temperature`: optional, Standard `0`
- `max_tokens`: optional, Standard `600`
- `headers`: optional fuer zusaetzliche HTTP-Header

## Empfehlung Fuer 48 GB VRAM

Mit `48 GB` VRAM hast du drei sinnvolle Profile:

- viele parallele Modelle: `3B` bis `8B`
- ausgewogener Mix: `12B` bis `14B`
- ein sehr starkes Einzelmodell: `24B` bis `35B`, in Grenzfaellen `70B` in aggressiver Quantisierung

Voreinstellung in [models.example.json](models.example.json):

- `qwen2.5:3b` fuer schnelle allgemeine Antworten
- `qwen2.5:7b` als guter Allrounder
- `qwen2.5-coder:7b` fuer Coding
- `deepseek-r1:8b` fuer Reasoning
- `command-r7b:7b` fuer RAG und Tool-Use
- `gemma3:4b` fuer kompaktes multilinguales Modell
- `llama3.1:8b` als zweiter Allrounder
- optional deaktiviert: `mistral-nemo:12b`, `phi4:14b`, `granite3.3:8b`

Diese Modellgroessen liegen laut den aktuellen Ollama-Library-Seiten vom `5. April 2026` grob bei:

- `qwen2.5:3b`: ca. `1.9 GB`
- `qwen2.5:7b`: ca. `4.7 GB`
- `qwen2.5-coder:7b`: ca. `4.7 GB`
- `deepseek-r1:8b`: ca. `5.2 GB`
- `command-r7b:7b`: ca. `5.1 GB`
- `gemma3:4b`: ca. `3.3 GB`
- `llama3.1:8b`: ca. `4.9 GB`
- `mistral-nemo:12b`: ca. `7.1 GB`
- `phi4:14b`: ca. `9.1 GB`
- `granite3.3:8b`: ca. `4.9 GB`

Alle aktivierten Standardmodelle zusammen liegen grob bei rund `29.9 GB` Modellgewicht. Das ist auf `48 GB` fuer parallelen Inference-Betrieb realistisch. Das ist eine Inferenz aus den offiziellen Modellgroessen; der echte Bedarf haengt von Quantisierung, Kontextlaenge und Anzahl gleichzeitiger Requests ab.

Standardmodell-Set laden:

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:8b
ollama pull command-r7b:7b
ollama pull gemma3:4b
ollama pull llama3.1:8b
```

Danach:

```bash
ollama list
```

Wenn du lieber nur drei Modelle parallel fahren willst, wuerde ich diese Auswahl nehmen:

- `qwen2.5:7b`
- `qwen2.5-coder:7b`
- `deepseek-r1:8b` oder `gemma3:4b`

Alle Modelle aus `models.example.json` laden:

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:8b
ollama pull command-r7b:7b
ollama pull mistral-nemo:12b
ollama pull phi4:14b
ollama pull gemma3:4b
ollama pull llama3.1:8b
ollama pull granite3.3:8b
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:14b
ollama pull deepseek-r1:14b
ollama pull gemma3:12b
ollama pull mistral-small:24b
ollama pull command-r:35b
ollama pull qwen2.5:32b
ollama pull qwen2.5-coder:32b
ollama pull deepseek-r1:32b
ollama pull gemma3:27b
ollama pull llama3.1:70b-text-q4_K_S
```

Wenn du wirklich alle Modelle ziehst, brauchst du entsprechend viel SSD-Speicher. Fuer `48 GB` VRAM ist das sinnvoll als Modellpool, aber nicht als gleichzeitig aktivierter Inference-Mix.

## Groessere Und Diversere Modelle

In [models.example.json](/Users/ssl/Documents/github/multi-llm-responder/models.example.json) findest du jetzt auch die groesseren und diverseren Modelle:

- `qwen2.5:14b` fuer allgemein starke Antworten
- `qwen2.5-coder:14b` fuer staerkere Coding-Qualitaet
- `deepseek-r1:14b` fuer Reasoning
- `gemma3:12b` fuer multilingual plus spaeter Vision
- optional deaktiviert: `mistral-small:24b`, `command-r:35b`, `qwen2.5:32b`, `qwen2.5-coder:32b`, `deepseek-r1:32b`, `gemma3:27b`, `llama3.1:70b-text-q4_K_S`

Ein guter 48-GB-Start fuer dieses groessere Profil ist:

```bash
ollama pull qwen2.5:14b
ollama pull qwen2.5-coder:14b
ollama pull deepseek-r1:14b
ollama pull gemma3:12b
uv run python -m multi_llm_responder --config models.example.json "Hallo Welt"
```

Wenn du eines der deaktivierten grossen Modelle testen willst, setze in `models.example.json` das jeweilige `enabled` auf `true` und deaktiviere andere schwere Modelle entsprechend. Fuer `32B` bis `70B` solltest du in der Praxis meist nur `1` bis `2` solche Modelle gleichzeitig aktiv haben.

## Troubleshooting

Wenn du `Connection refused` auf Ubuntu siehst, ist fast immer der lokale Ollama-Dienst nicht gestartet oder die `base_url` zeigt auf den falschen Host.

Pruefen, ob Ollama antwortet:

```bash
curl http://127.0.0.1:11434/api/tags
```

Falls keine Antwort kommt, starte Ollama:

```bash
ollama serve
```

Falls Ollama als Service installiert ist, kannst du je nach Setup auch pruefen:

```bash
systemctl status ollama
```

Wenn dein Modellserver auf einem anderen Rechner oder Container laeuft, ersetze in `models.example.json` die `base_url` von `http://127.0.0.1:11434` auf die echte Host-IP, zum Beispiel `http://192.168.1.50:11434`.

Wenn du `HTTP 404: model '...' not found` siehst, laeuft Ollama zwar, aber das Modell wurde noch nicht mit `ollama pull ...` heruntergeladen.

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
