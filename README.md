# Local Conversation Processing and Compression System

A local-first full-stack Sem-EL project that cleans long conversations, detects duplicate statements, groups information by topic, identifies possible correction candidates, preserves a reviewable history, creates compact summaries, chunks content, reports metrics, and exports TXT/JSON.

## Features

- React + Vite responsive dashboard.
- FastAPI backend with Pydantic request validation.
- Local SQLite persistence for original conversations, processing results, and correction resolutions.
- Text normalization and sentence segmentation that retain source wording.
- Exact/case-insensitive duplicate detection and near-duplicate candidate detection.
- Rule-based topic classification, important-context extraction, and structured summary.
- Subject-filtered correction candidates; candidates remain pending until a user resolves them.
- Accept/reject/unresolved correction review; accepted earlier statements are marked superseded in the current summary while retained in source/history.
- Configurable compression level, chunk size, similarity threshold, and correction context window.
- Word counts, rough token estimates, duplicate/correction/chunk counts, reduction percentages.
- TXT/JSON exports, source traceability, conversation history, and delete action.
- Pytest tests for the processing pipeline and correction edge cases.

## Architecture

```text
frontend/ (React + Vite)
  └── HTTP JSON requests
backend/app/main.py (FastAPI routes)
  ├── schemas.py (Pydantic)
  ├── database.py (SQLite persistence)
  └── processing/
      ├── preprocess.py
      ├── duplicates.py
      ├── classifier.py
      ├── corrections.py
      ├── summarizer.py
      ├── chunking.py
      ├── metrics.py
      └── pipeline.py
```

## Requirements

- Python 3.10+ (3.11 recommended)
- Node.js 20+ and npm
- Windows, macOS, or Linux

No API key is needed. The default processing pipeline is local and rule-based. Optional local NLI support is available through `backend/requirements-nli.txt`; set `ENABLE_LOCAL_NLI=1` before starting the backend to attempt loading `cross-encoder/nli-deberta-v3-xsmall` on CPU. The model may need to be downloaded once into the local model cache. If the dependency, model, or download is unavailable, processing falls back to rules without inventing NLI scores.

## Run on Windows PowerShell

Open two terminals in the project folder.

### 1. Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend health: <http://127.0.0.1:8000/api/health>
Interactive API docs: <http://127.0.0.1:8000/docs>

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again. Alternatively, use `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe -m uvicorn app.main:app --reload` without activation.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually <http://localhost:5173>.


### Optional local NLI model

Install optional dependencies from the `backend` directory:

```powershell
pip install -r requirements-nli.txt
$env:ENABLE_LOCAL_NLI = "1"
$env:LOCAL_NLI_MODEL = "cross-encoder/nli-deberta-v3-xsmall"
uvicorn app.main:app --reload
```

The first model load may need internet access to fetch model files. Once cached, inference is local. If loading fails, the application continues with rule-based detection. Do not interpret model probabilities as proof that a correction is true; the review UI remains authoritative.

## Run tests

From the `backend` directory, with the virtual environment active:

```powershell
pytest -q
```

## Demo workflow

1. Start backend and frontend.
2. Click **Load sample**.
3. Click **Process conversation**.
4. Check summary, important context, topic groups, correction candidates, chunks, and metrics.
5. Accept/reject candidates only after reviewing the before/after statements.
6. Export TXT or JSON, then open a saved conversation from Recent conversations.

The demonstration input intentionally includes two schedule/deadline revisions and two unrelated task assignments. The detector should suggest the revisions and avoid pairing the unrelated task assignments.

## API endpoints

- `GET /api/health`
- `POST /api/process`
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `DELETE /api/conversations/{id}`
- `GET /api/conversations/{id}/corrections`
- `POST /api/conversations/{id}/corrections/{index}/resolve` with `{"status":"accepted|rejected|unresolved"}`
- `GET /api/conversations/{id}/export?format=txt|json`

## Data and privacy

The SQLite database is created at `backend/data/conversations.db`. Original conversation text is stored to support source inspection and history. Use the delete action to delete a conversation and its linked correction resolution records. Avoid putting sensitive content into shared machines. This implementation makes no cloud inference calls; browser fonts may be fetched from Google Fonts while online. For a fully offline UI, replace the remote font import in `frontend/src/styles.css` with local/system fonts.

## Metric definitions

- Word reduction = `(original words - summary words) / original words × 100`; safe for zero-word input.
- Token counts are rough estimates (`whitespace words × 1.33`), not tokenizer-exact counts.
- Exact duplicates are statements with identical normalized text after case/punctuation normalization.
- Near-duplicates are similarity candidates and are not automatically removed.
- Correction candidates are proposals, not verified truth. A user resolution is required before an earlier statement is treated as superseded.

## Current limitations

- Topic classification and correction detection are heuristic and may miss paraphrases or flag edge cases; review is required.
- The optional NLI model is disabled by default and may be too slow for large inputs on CPU; enable it only when dependencies and model weights are available. Rule-based subject matching remains a heuristic.
- Sentence splitting is lightweight and may split unusual abbreviations imperfectly.
- High compression filters categories but does not use a generative model.
- React component test framework is not configured; backend processing and API behavior are the initial automated-test focus.
- The resolution endpoint rebuilds current summary sections from retained statements; a later improvement should recalculate every derived metric and topic/context field after each correction resolution.

## Team contributions

Fill in each member's name and actual contribution before submission. Do not claim a contribution that was not performed.

- Member 1: ____________________
- Member 2: ____________________
- Member 3: ____________________
- Member 4: ____________________

## License

Academic project starter. Add a license if your team chooses to publish/reuse it.
