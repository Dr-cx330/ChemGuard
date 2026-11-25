# ChemGuard

A conservative, simulation-only FastAPI gateway for proposed laboratory operations. This prototype does not connect to, control, or approve real instruments. `ALLOW` is reserved for future reviewed rules; current operations return `HOLD` or `DENY`.

## Windows setup

Requires Python 3.10 or newer.

```powershell
cd C:\Users\Administrator\Desktop\768\ChemGuard
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run and verify

```powershell
uvicorn chemguard.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the API. Health check: `GET /health`.

## ChatGPT API bridge (local demo)

Set an OpenAI API key in the PowerShell window (API usage may be billed separately from a ChatGPT subscription):

```powershell
$env:OPENAI_API_KEY = "your-api-key"
uvicorn chemguard.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The chat page sends each message to the Responses API to extract a structured operation proposal, then always passes any proposal through ChemGuard and displays the decision. It does not execute operations. The API key stays on the local server and is not sent to the browser. To select a different supported model, set `CHEMGUARD_MODEL` before starting the server. This is a separate API-powered chat demo, not a plug-in to the consumer ChatGPT website.

```powershell
pytest
```

Example request:

```json
{
  "device_id": "Reactor_01",
  "action": "stir",
  "parameters": {"rpm": 200, "temperature_c": 80, "volume_ml": 50},
  "duration_seconds": 600,
  "chemicals": ["ethanol"],
  "description": "Heat ethanol while stirring"
}
```

Send it as JSON to `POST /api/v1/evaluate`. Each evaluation is written to a local SQLite audit database. The gateway never translates a decision into device commands. Do not connect a real instrument to this prototype; actual deployments require independent hardware interlocks, qualified process safety review, access control, and instrument-specific validation.
