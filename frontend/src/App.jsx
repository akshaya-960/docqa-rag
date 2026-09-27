import { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim()) return;

    const userMessage = { role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.text }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, sources: data.sources, tool: data.used_tool },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error reaching the backend. Is it running on :8000?" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploadStatus(`Uploading ${file.name}...`);

    try {
      const res = await fetch(`${API_BASE}/ingest`, { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`Ingested ${data.document} (${data.chunks_created} chunks)`);
      } else {
        setUploadStatus(`Error: ${data.detail}`);
      }
    } catch {
      setUploadStatus("Upload failed. Is the backend running?");
    }
  }

  return (
    <div className="app">
      <header>
        <h1>DocQA</h1>
        <p className="subtitle">Ask questions grounded in your own documents.</p>
      </header>

      <div className="upload-row">
        <label htmlFor="file-upload" className="upload-label">
          Upload a document
        </label>
        <input id="file-upload" type="file" accept=".pdf,.txt" onChange={handleUpload} />
        {uploadStatus && <span className="upload-status">{uploadStatus}</span>}
      </div>

      <div className="chat-window">
        {messages.length === 0 && (
          <p className="empty-state">Ingest a document, then ask a question about it below.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <p>{m.text}</p>
            {m.tool && <span className="tool-tag">via {m.tool}</span>}
            {m.sources && m.sources.length > 0 && (
              <details>
                <summary>{m.sources.length} source(s)</summary>
                {m.sources.map((s, j) => (
                  <div key={j} className="source">
                    <strong>{s.document} — chunk {s.chunk_index}</strong>
                    <p>{s.text}</p>
                  </div>
                ))}
              </details>
            )}
          </div>
        ))}
        {loading && <p className="loading">Thinking…</p>}
      </div>

      <form className="ask-row" onSubmit={handleAsk}>
        <input
          type="text"
          placeholder="Ask a question…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          Ask
        </button>
      </form>
    </div>
  );
}
