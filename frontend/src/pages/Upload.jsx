import { useState, useEffect } from 'react';
import { fetchJson, postForm, deleteRequest } from '../api';

export default function Upload() {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState('');
  const [trueText, setTrueText] = useState('');
  const [trueSummary, setTrueSummary] = useState('');
  const [trueTopic, setTrueTopic] = useState('');
  const [subjectArea, setSubjectArea] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const loadNotes = () => fetchJson('/api/notes').then(setNotes);

  useEffect(() => { loadNotes(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !trueText.trim()) {
      setMsg('Title and text are required.');
      return;
    }
    setSaving(true);
    setMsg('');
    const form = new FormData();
    form.append('title', title);
    form.append('true_text', trueText);
    if (trueSummary) form.append('true_summary', trueSummary);
    if (trueTopic) form.append('true_topic', trueTopic);
    if (subjectArea) form.append('subject_area', subjectArea);
    try {
      await postForm('/api/notes', form);
      setTitle(''); setTrueText(''); setTrueSummary(''); setTrueTopic(''); setSubjectArea('');
      setMsg('Note saved successfully!');
      loadNotes();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this note and all its experiments?')) return;
    await deleteRequest(`/api/notes/${id}`);
    loadNotes();
  };

  return (
    <>
      <h1 className="page-title">Upload Ground Truth Notes</h1>
      <p className="page-subtitle">Add clinical notes to use in pipeline experiments</p>

      <div className="two-col">
        <div className="chart-section">
          <h3>New Note</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Discharge Summary #1" />
            </div>
            <div className="form-group">
              <label>True Text *</label>
              <textarea value={trueText} onChange={(e) => setTrueText(e.target.value)}
                        placeholder="Paste the ground truth clinical text here..." />
            </div>
            <div className="form-group">
              <label>True Summary (optional)</label>
              <textarea value={trueSummary} onChange={(e) => setTrueSummary(e.target.value)}
                        placeholder="Expected summary for ROUGE evaluation" style={{ minHeight: 80 }} />
            </div>
            <div className="form-group">
              <label>True Topic (optional)</label>
              <input value={trueTopic} onChange={(e) => setTrueTopic(e.target.value)}
                     placeholder="e.g. cardiology, neurology" />
            </div>
            <div className="form-group">
              <label>Subject Area (optional)</label>
              <input value={subjectArea} onChange={(e) => setSubjectArea(e.target.value)}
                     placeholder="e.g. Internal Medicine" />
            </div>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save Note'}
            </button>
            {msg && <p style={{ marginTop: 10, color: msg.startsWith('Error') ? '#e84c4c' : '#51cf66' }}>{msg}</p>}
          </form>
        </div>

        <div className="chart-section">
          <h3>Existing Notes ({notes.length})</h3>
          {notes.length === 0 ? (
            <p style={{ color: '#6b7599' }}>No notes uploaded yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {notes.map((n) => (
                <div key={n.id} style={{
                  background: '#161926', border: '1px solid #2e3250', borderRadius: 8, padding: 14,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>{n.title}</strong>
                    <button className="btn danger" style={{ padding: '4px 10px', fontSize: 12 }}
                            onClick={() => handleDelete(n.id)}>Delete</button>
                  </div>
                  <p style={{ color: '#6b7599', fontSize: 13, marginTop: 4 }}>
                    {n.true_text.slice(0, 120)}{n.true_text.length > 120 ? '...' : ''}
                  </p>
                  {n.true_topic && <span style={{ fontSize: 12, color: '#4c9be8' }}>Topic: {n.true_topic}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
