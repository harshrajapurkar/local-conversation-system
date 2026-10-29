import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from .schemas import ProcessRequest, ResolveRequest
from .processing.pipeline import process_conversation
from . import database

app = FastAPI(title="Local Conversation Processing and Compression System", version="1.0.0", description="Local-first conversation compression and correction review API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup(): database.init_db()

@app.get("/api/health")
def health(): return {"status": "ok", "storage": "local SQLite", "inference": "rule-based local processing; optional NLI model not loaded"}

@app.post("/api/process")
def process(req: ProcessRequest):
    try: result = process_conversation(req.text, req.compression, req.max_chunk_words, req.similarity_threshold, req.context_window)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    cid = database.save_conversation(req.title, req.text, result) if req.save else None
    return {"id": cid, "title": req.title, **result}

@app.get("/api/conversations")
def conversations(): return database.list_conversations()

@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: int):
    item = database.get_conversation(conversation_id)
    if item is None: raise HTTPException(status_code=404, detail="Conversation not found")
    return item

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    if not database.delete_conversation(conversation_id): raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True, "id": conversation_id}

@app.get("/api/conversations/{conversation_id}/corrections")
def corrections(conversation_id: int):
    item = database.get_conversation(conversation_id)
    if item is None: raise HTTPException(status_code=404, detail="Conversation not found")
    return item["summary"]["corrections"]

@app.post("/api/conversations/{conversation_id}/corrections/{correction_index}/resolve")
def resolve(conversation_id: int, correction_index: int, req: ResolveRequest):
    try: result = database.resolve_correction(conversation_id, correction_index, req.status)
    except IndexError as exc: raise HTTPException(status_code=404, detail=str(exc))
    if result is None: raise HTTPException(status_code=404, detail="Conversation not found")
    return result["summary"]

@app.get("/api/conversations/{conversation_id}/export")
def export_conversation(conversation_id: int, format: str = "txt"):
    item = database.get_conversation(conversation_id)
    if item is None: raise HTTPException(status_code=404, detail="Conversation not found")
    if format == "json": return JSONResponse(content=item, headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id}.json"'})
    if format != "txt": raise HTTPException(status_code=400, detail="format must be txt or json")
    summary = item["summary"]
    lines = [f"{item['title']}", "=" * len(item['title']), "", "SUMMARY", summary.get("summary_text", ""), "", "IMPORTANT CONTEXT"]
    lines.extend(f"- {x}" for x in summary.get("important_context", []))
    lines += ["", "CORRECTION HISTORY"]
    for event in summary.get("corrections", []):
        lines += [f"- Status: {event.get('review_status')}", f"  Earlier: {event.get('earlier_statement')}", f"  Latest: {event.get('newer_statement')}"]
    lines += ["", "PROCESSING METRICS", json.dumps(item.get("metrics", {}), indent=2)]
    return PlainTextResponse("\n".join(lines), headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id}.txt"'})
