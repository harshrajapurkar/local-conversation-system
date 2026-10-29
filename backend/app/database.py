import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "conversations.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS conversations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, original_text TEXT NOT NULL,
          result_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS correction_resolutions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL,
          correction_index INTEGER NOT NULL, status TEXT NOT NULL CHECK(status IN ('accepted','rejected','unresolved')),
          updated_at TEXT NOT NULL, UNIQUE(conversation_id, correction_index),
          FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        ''')

def save_conversation(title, original_text, result):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute("INSERT INTO conversations(title, original_text, result_json, created_at, updated_at) VALUES(?,?,?,?,?)", (title[:120] or "Untitled conversation", original_text, json.dumps(result, ensure_ascii=False), now, now))
        return cur.lastrowid

def list_conversations():
    with connect() as db:
        rows = db.execute("SELECT id,title,created_at,updated_at,length(original_text) AS characters FROM conversations ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def get_conversation(cid):
    with connect() as db:
        row = db.execute("SELECT * FROM conversations WHERE id=?", (cid,)).fetchone()
        if not row: return None
        result = json.loads(row["result_json"])
        resolutions = db.execute("SELECT correction_index,status FROM correction_resolutions WHERE conversation_id=?", (cid,)).fetchall()
        for resolution in resolutions:
            idx, status = resolution["correction_index"], resolution["status"]
            if idx < len(result["summary"]["corrections"]):
                result["summary"]["corrections"][idx]["review_status"] = status
                result["summary"]["corrections"][idx]["resolution"] = status
        return {"id": row["id"], "title": row["title"], "created_at": row["created_at"], "updated_at": row["updated_at"], **result}

def resolve_correction(cid, index, status):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        row = db.execute("SELECT result_json FROM conversations WHERE id=?", (cid,)).fetchone()
        if not row: return None
        result = json.loads(row["result_json"])
        corrections = result.get("summary", {}).get("corrections", [])
        if index < 0 or index >= len(corrections): raise IndexError("Correction index does not exist")
        corrections[index]["review_status"] = status
        corrections[index]["resolution"] = status
        if status == "accepted":
            earlier = corrections[index]["earlier_statement_id"]
            result["summary"]["superseded_statement_ids"] = sorted(set(result["summary"].get("superseded_statement_ids", [])) | {earlier})
        elif status == "rejected":
            earlier = corrections[index]["earlier_statement_id"]
            still_accepted = any(c.get("earlier_statement_id") == earlier and c.get("review_status") == "accepted" for c in corrections)
            if not still_accepted:
                result["summary"]["superseded_statement_ids"] = [x for x in result["summary"].get("superseded_statement_ids", []) if x != earlier]
        result["summary"]["pending_conflicts"] = [c for c in corrections if c.get("review_status") in {"pending_review", "unresolved"}]
        # Rebuild current summary based on accepted correction decisions.
        superseded = set(result["summary"].get("superseded_statement_ids", []))
        statements = [s for s in result["statements"] if not s.get("duplicate_of") and s["id"] not in superseded]
        sections = {}
        for s in statements: sections.setdefault(s["category"], []).append(s["text"])
        result["summary"]["sections"] = sections
        result["summary"]["summary_text"] = "\n".join(f"{k}\n" + "\n".join(f"- {v}" for v in vals) for k, vals in sections.items())
        db.execute("UPDATE conversations SET result_json=?, updated_at=? WHERE id=?", (json.dumps(result, ensure_ascii=False), now, cid))
        db.execute("INSERT INTO correction_resolutions(conversation_id,correction_index,status,updated_at) VALUES(?,?,?,?) ON CONFLICT(conversation_id,correction_index) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at", (cid,index,status,now))
        return result

def delete_conversation(cid):
    with connect() as db:
        cur = db.execute("DELETE FROM conversations WHERE id=?", (cid,))
        return cur.rowcount > 0
