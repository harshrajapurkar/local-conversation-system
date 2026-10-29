import React, { useEffect, useMemo, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const sample = `The team meeting is planned for Wednesday at 2 PM.
Priya will complete the database schema.
The final submission deadline is Saturday.
Actually, the team meeting has been moved to Thursday at 4 PM.
Rahul will test the registration page.
The API documentation must be ready by Thursday.
The API documentation must be ready by Friday, not Thursday.`;

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response;
}
function Stat({ label, value, hint }) { return <div className="stat"><div className="stat-label">{label}</div><div className="stat-value">{value ?? '—'}</div>{hint && <div className="stat-hint">{hint}</div>}</div>; }
function downloadText(filename, text, type='text/plain') { const url = URL.createObjectURL(new Blob([text], {type})); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url); }

export default function App() {
  const [text, setText] = useState('');
  const [title, setTitle] = useState('My conversation');
  const [compression, setCompression] = useState('balanced');
  const [chunkWords, setChunkWords] = useState(180);
  const [threshold, setThreshold] = useState(0.9);
  const [contextWindow, setContextWindow] = useState(8);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [tab, setTab] = useState('summary');
  const [health, setHealth] = useState('checking');
  const [activeChunk, setActiveChunk] = useState(0);

  const refreshHistory = async () => { try { setHistory(await (await request('/api/conversations')).json()); } catch {} };
  useEffect(() => { request('/api/health').then(() => setHealth('online')).catch(() => setHealth('offline')); refreshHistory(); }, []);
  const metrics = result?.metrics;
  const corrections = result?.summary?.corrections || [];
  const currentSummary = result?.summary?.summary_text || '';

  async function process() {
    setError(''); setNotice('');
    if (!text.trim()) { setError('Paste a conversation or load the sample before processing.'); return; }
    setBusy(true);
    try {
      const response = await request('/api/process', { method: 'POST', body: JSON.stringify({ text, title, compression, max_chunk_words: Number(chunkWords), similarity_threshold: Number(threshold), context_window: Number(contextWindow), save: true }) });
      const data = await response.json(); setResult(data); setTab('summary'); setActiveChunk(0); setNotice('Conversation processed and saved locally.'); refreshHistory();
    } catch (e) { setError(e.message || 'Processing failed. Check that the backend is running.'); }
    finally { setBusy(false); }
  }
  async function openHistory(id) {
    setError(''); setNotice('');
    try { const data = await (await request(`/api/conversations/${id}`)).json(); setResult(data); setText(data.original_text || ''); setTitle(data.title || 'Saved conversation'); setTab('summary'); setActiveChunk(0); }
    catch (e) { setError(e.message); }
  }
  async function resolveCorrection(index, status) {
    if (!result?.id) return;
    setError('');
    try {
      await request(`/api/conversations/${result.id}/corrections/${index}/resolve`, { method: 'POST', body: JSON.stringify({status}) });
      const updated = await (await request(`/api/conversations/${result.id}`)).json(); setResult(updated); setNotice(`Correction marked ${status.replace('_',' ')}.`); refreshHistory();
    } catch (e) { setError(e.message); }
  }
  async function deleteHistory(id) {
    if (!confirm('Delete this conversation and its saved processing records? This cannot be undone.')) return;
    try { await request(`/api/conversations/${id}`, {method:'DELETE'}); if (result?.id === id) setResult(null); setNotice('Conversation deleted from local storage.'); refreshHistory(); }
    catch (e) { setError(e.message); }
  }
  async function exportSaved(format) {
    if (!result?.id) return;
    try { const response = await request(`/api/conversations/${result.id}/export?format=${format}`); const blob = await response.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=`conversation-${result.id}.${format}`; a.click(); URL.revokeObjectURL(url); }
    catch (e) { setError(e.message); }
  }
  function uploadFile(event) {
    const file = event.target.files?.[0]; if (!file) return;
    if (!file.name.toLowerCase().endsWith('.txt')) { setError('Only .txt files are supported.'); event.target.value=''; return; }
    if (file.size > 2_000_000) { setError('File is too large. Please use a TXT file smaller than 2 MB.'); event.target.value=''; return; }
    const reader = new FileReader(); reader.onload = () => { setText(String(reader.result || '')); setError(''); setNotice(`Loaded ${file.name}`); }; reader.onerror = () => setError('Could not read this file.'); reader.readAsText(file); event.target.value='';
  }

  return <div className="app-shell">
    <header className="topbar"><div className="brand"><div className="brand-mark">LC</div><div><div className="brand-title">Local Context</div><div className="brand-subtitle">Conversation processing & compression</div></div></div><div className={`status-pill ${health}`}><span className="status-dot" />Backend {health}</div></header>
    <main className="page">
      <section className="hero"><div className="eyebrow"><span className="eyebrow-dot"/> LOCAL-FIRST WORKSPACE</div><h1>Keep the context.<br/><span>Lose the repetition.</span></h1><p>Turn long conversations into structured, traceable context. Review possible corrections before changing what counts as current.</p><div className="hero-tags"><span>◈ On-device workflow</span><span>▤ Auditable history</span><span>⌁ No paid API keys</span></div></section>
      {error && <div className="alert error"><strong>Something needs attention</strong><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss">×</button></div>}
      {notice && <div className="alert success"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss">×</button></div>}
      <section className="workspace-grid">
        <div className="panel input-panel"><div className="panel-heading"><div><div className="section-kicker">01 / INPUT</div><h2>Conversation source</h2></div><span className="mini-badge">Private by design</span></div>
          <label className="field-label" htmlFor="conversation-title">Conversation title</label><input id="conversation-title" className="text-input" value={title} maxLength={120} onChange={e=>setTitle(e.target.value)} placeholder="e.g. Project planning meeting"/>
          <div className="editor-heading"><label className="field-label" htmlFor="conversation-text">Paste conversation</label><span>{text.length.toLocaleString()} characters</span></div><textarea id="conversation-text" className="conversation-editor" value={text} onChange={e=>setText(e.target.value)} placeholder="Paste your conversation here. Keep the original wording; the system will preserve it for traceability." />
          <div className="editor-actions"><label className="button secondary upload-button">↑ Upload TXT<input type="file" accept=".txt,text/plain" onChange={uploadFile} hidden/></label><button className="button secondary" onClick={()=>{setText(sample);setTitle('Correction detection demo');setError('');setNotice('Sample conversation loaded.');}}>Load sample</button><button className="text-button" onClick={()=>{setText('');setError('');setNotice('Editor cleared.');}}>Clear</button></div>
          <div className="settings"><div className="settings-title">Processing settings</div><div className="setting-row"><div><label htmlFor="compression">Compression level</label><small>Controls how much unique detail is retained.</small></div><select id="compression" value={compression} onChange={e=>setCompression(e.target.value)}><option value="low">Low — preserve detail</option><option value="balanced">Balanced — recommended</option><option value="high">High — shorter summary</option></select></div>
          <div className="setting-row"><div><label htmlFor="chunk">Chunk size</label><small>Maximum target words per chunk.</small></div><input id="chunk" type="number" min="1" max="10000" value={chunkWords} onChange={e=>setChunkWords(e.target.value)}/></div>
          <div className="setting-row"><div><label htmlFor="threshold">Near-duplicate threshold</label><small>Higher values require closer wording.</small></div><div className="range-control"><input id="threshold" type="range" min="0.5" max="0.99" step="0.01" value={threshold} onChange={e=>setThreshold(e.target.value)}/><span>{Number(threshold).toFixed(2)}</span></div></div>
          <div className="setting-row"><div><label htmlFor="window">Correction context window</label><small>How many earlier statements to compare.</small></div><input id="window" type="number" min="1" max="50" value={contextWindow} onChange={e=>setContextWindow(e.target.value)}/></div></div>
          <button className="button primary process-button" onClick={process} disabled={busy || health==='offline'}>{busy ? <><span className="spinner"/> Processing locally…</> : <>Process conversation <span>→</span></>}</button>
          {health==='offline' && <p className="offline-note">Start the Python backend to enable processing.</p>}
        </div>
        <div className="right-column">
          <div className="panel privacy-panel"><div className="privacy-icon">⌂</div><div><h3>Your text stays local</h3><p>Processing runs through your local backend. Saved conversations live in a local SQLite database on this computer. No paid inference API is used.</p></div></div>
          <div className="panel history-panel"><div className="panel-heading"><div><div className="section-kicker">LOCAL DATABASE</div><h2>Recent conversations</h2></div><button className="icon-button" title="Refresh history" onClick={refreshHistory}>↻</button></div>
            {history.length===0 ? <div className="empty-history"><div className="empty-icon">▤</div><strong>No saved conversations yet</strong><span>Processed conversations will appear here.</span></div> : <div className="history-list">{history.map(item=><div className={`history-item ${result?.id===item.id?'selected':''}`} key={item.id}><button className="history-open" onClick={()=>openHistory(item.id)}><span className="history-file">▤</span><span className="history-info"><strong>{item.title}</strong><small>{new Date(item.created_at).toLocaleString()} · {item.characters.toLocaleString()} chars</small></span></button><button className="delete-button" title="Delete conversation" onClick={()=>deleteHistory(item.id)}>×</button></div>)}</div>}
            <div className="history-footnote">Saved data is local to this application instance.</div>
          </div>
          <div className="panel workflow-panel"><div className="section-kicker">PIPELINE</div><h3>What happens to your text?</h3><div className="pipeline">{['Clean & segment','Find duplicates','Group by topic','Review possible corrections','Summarize & chunk','Measure & export'].map((step,i)=><div className="pipeline-step" key={step}><span>{String(i+1).padStart(2,'0')}</span>{step}</div>)}</div></div>
        </div>
      </section>
      {result && <section className="results-section" id="results"><div className="results-header"><div><div className="section-kicker">02 / ANALYSIS RESULTS</div><h2>{result.title || title}</h2><p>Generated from your submitted conversation. Review pending correction candidates before relying on them.</p></div><div className="export-actions"><button className="button secondary" onClick={()=>exportSaved('txt')}>↓ Export TXT</button><button className="button secondary" onClick={()=>exportSaved('json')}>↓ Export JSON</button></div></div>
        <div className="stats-grid"><Stat label="Original words" value={metrics?.original_word_count?.toLocaleString()}/><Stat label="Summary words" value={metrics?.summary_word_count?.toLocaleString()}/><Stat label="Word reduction" value={`${metrics?.word_reduction_percent ?? 0}%`} hint="Original vs summary"/><Stat label="Duplicates removed" value={metrics?.exact_duplicates_removed ?? 0}/><Stat label="Correction candidates" value={metrics?.correction_candidates ?? 0}/><Stat label="Chunks generated" value={metrics?.chunks_generated ?? 0}/></div>
        <div className="tabs" role="tablist">{[['summary','Summary'],['context','Important context'],['topics','Topic groups'],['corrections',`Corrections (${corrections.length})`],['chunks',`Chunks (${result.chunks?.length||0})`],['metrics','Metrics & source']].map(([id,label])=><button key={id} role="tab" aria-selected={tab===id} className={tab===id?'active':''} onClick={()=>setTab(id)}>{label}</button>)}</div>
        <div className="panel result-panel">
          {tab==='summary' && <div className="summary-view"><div className="result-subhead"><div><span className="section-kicker">CURRENT COMPACT CONTEXT</span><h3>Structured summary</h3></div><button className="text-button" onClick={()=>downloadText('conversation-summary.txt',currentSummary)}>Copy as file ↓</button></div>{currentSummary ? <pre className="summary-text">{currentSummary}</pre> : <p className="muted">No summary statements were generated for this input.</p>}<div className="info-note"><span>ⓘ</span><p>Only corrections you accept are applied as superseded information. Pending candidates remain visible for review.</p></div></div>}
          {tab==='context' && <div><div className="result-subhead"><div><span className="section-kicker">KEEP FOR LATER</span><h3>Important context</h3></div><span className="count-badge">{result.summary?.important_context?.length||0} items</span></div>{(result.summary?.important_context||[]).length ? <ul className="context-list">{result.summary.important_context.map((item,i)=><li key={i}><span className="bullet-check">✓</span>{item}</li>)}</ul> : <p className="muted">No items were marked as important.</p>}</div>}
          {tab==='topics' && <div><div className="result-subhead"><div><span className="section-kicker">ORGANIZED STATEMENTS</span><h3>Topic groups</h3></div></div><div className="topic-grid">{Object.entries(result.summary?.topic_groups||{}).map(([category,items])=><div className="topic-card" key={category}><div className="topic-title"><strong>{category}</strong><span>{items.length}</span></div>{items.map(item=><div className="topic-item" key={item.id}><p>{item.text}</p><small>Source statement #{item.source_index+1}</small></div>)}</div>)}</div></div>}
          {tab==='corrections' && <div><div className="result-subhead"><div><span className="section-kicker">HUMAN REVIEW REQUIRED</span><h3>Correction history & conflicts</h3></div><span className="count-badge">{corrections.filter(c=>['pending_review','unresolved'].includes(c.review_status)).length} pending</span></div><div className="warning-note">These are candidates, not guaranteed corrections. Accept only when the newer statement really updates the same subject or event.</div>{corrections.length===0 ? <div className="empty-state"><strong>No correction candidates detected</strong><p>The rule-based detector did not find a likely correction pair.</p></div> : <div className="correction-list">{corrections.map((c,i)=><article className="correction-card" key={`${c.earlier_statement_id}-${c.newer_statement_id}-${i}`}><div className="correction-top"><span className={`status-tag ${c.review_status}`}>{(c.review_status||'pending_review').replaceAll('_',' ')}</span><span className="event-type">{(c.event_type||'candidate').replaceAll('_',' ')}</span></div><div className="version-grid"><div className="version old"><small>EARLIER STATEMENT · #{c.original_statement_index+1}</small><p>{c.earlier_statement}</p></div><div className="version new"><small>NEWER STATEMENT · #{c.new_statement_index+1}</small><p>{c.newer_statement}</p></div></div><div className="correction-meta"><span>Method: {c.detection_method}</span><span>Subject match: {Math.round((c.subject_similarity||0)*100)}%</span>{c.contradiction_confidence!=null && <span>NLI contradiction: {Math.round(c.contradiction_confidence*100)}%</span>}</div>{c.review_status==='pending_review' || c.review_status==='unresolved' ? <div className="review-actions"><button className="button accept" onClick={()=>resolveCorrection(i,'accepted')}>✓ Accept correction</button><button className="button secondary" onClick={()=>resolveCorrection(i,'rejected')}>Reject</button><button className="text-button" onClick={()=>resolveCorrection(i,'unresolved')}>Keep unresolved</button></div> : <div className="resolved-note">This candidate has been {c.review_status}. You can reprocess the original conversation to create a fresh review.</div>}</article>)}</div>}</div>}
          {tab==='chunks' && <div><div className="result-subhead"><div><span className="section-kicker">STATEMENT-ALIGNED SPLITS</span><h3>Conversation chunks</h3></div><span className="count-badge">{result.chunks?.length||0} total</span></div>{!result.chunks?.length ? <p className="muted">No chunks were generated.</p> : <><div className="chunk-picker">{result.chunks.map((chunk,i)=><button className={activeChunk===i?'active':''} onClick={()=>setActiveChunk(i)} key={chunk.chunk_index}>Chunk {i+1}<small>{chunk.word_count} words</small></button>)}</div><div className="chunk-content"><div className="chunk-heading"><strong>Chunk {activeChunk+1}</strong><span>{result.chunks[activeChunk]?.word_count} words {result.chunks[activeChunk]?.oversized_statement?'· includes a statement larger than the target':''}</span></div>{(result.chunks[activeChunk]?.statements||[]).map((s,i)=><p className="chunk-statement" key={`${s.id}-${i}`}><span>#{s.source_index+1}</span>{s.text}</p>)}</div><button className="button secondary" onClick={()=>downloadText(`conversation-chunk-${activeChunk+1}.txt`,(result.chunks[activeChunk]?.statements||[]).map(s=>s.text).join('\n'))}>↓ Export this chunk</button></>}</div>}
          {tab==='metrics' && <div><div className="result-subhead"><div><span className="section-kicker">TRANSPARENT MEASUREMENTS</span><h3>Processing metrics</h3></div></div><div className="metrics-table">{Object.entries(metrics||{}).map(([key,value])=><div key={key}><span>{key.replaceAll('_',' ')}</span><strong>{typeof value==='number' ? value.toLocaleString() : String(value)}</strong></div>)}</div><div className="source-preview"><h4>Original source (preserved)</h4><pre>{result.original_text}</pre></div><div className="source-preview"><h4>Near-duplicate candidates</h4>{result.duplicates?.near_duplicates?.length ? result.duplicates.near_duplicates.map((d,i)=><p key={i}><strong>{Math.round(d.similarity*100)}% similar:</strong> “{d.text}”<br/><small>Compared with: “{d.matched_text}”</small></p>) : <p className="muted">No near-duplicate candidates detected at this threshold.</p>}</div><p className="disclaimer">Token counts are estimates, not output from a model-specific tokenizer. Automated summaries and correction candidates can miss nuance; verify important information.</p></div>}
        </div>
      </section>}
      <footer><div className="footer-brand">LC <span>Local Context</span></div><span>Local-first · Human-reviewed corrections · Source traceability</span></footer>
    </main>
  </div>;
}
