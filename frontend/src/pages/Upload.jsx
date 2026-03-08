import { useState, useEffect, useRef } from 'react';
import { fetchJson, postForm, deleteRequest } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Upload() {
  const [notes, setNotes] = useState([]);
  const [gallery, setGallery] = useState([]);
  const [tab, setTab] = useState('upload'); // upload | gallery

  // Form state
  const [title, setTitle] = useState('');
  const [trueText, setTrueText] = useState('');
  const [ocrText, setOcrText] = useState('');
  const [trueTopic, setTrueTopic] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const fileRef = useRef();

  const loadNotes = () => fetchJson('/api/notes').then(setNotes);
  const loadGallery = () => fetchJson('/api/documents/gallery/list').then(setGallery);

  useEffect(() => { loadNotes(); loadGallery(); }, []);

  // ── Handle image selection ──────────────────────────────────────────────
  const handleImageSelect = (file) => {
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setOcrText('');
    setMsg('');
  };

  const handleRunOCR = async () => {
    if (!imageFile) { setMsg('Select an image first.'); return; }
    setOcrLoading(true);
    setMsg('');
    const form = new FormData();
    form.append('image', imageFile);
    try {
      const res = await postForm('/api/notes/ocr-preview', form);
      setOcrText(res.ocr_text || '');
      setMsg('OCR complete! Review the text below.');
    } catch (err) {
      setMsg(`OCR Error: ${err.message}`);
    } finally {
      setOcrLoading(false);
    }
  };

  // ── Use gallery image ───────────────────────────────────────────────────
  const handleGallerySelect = async (item) => {
    setTab('upload');
    setMsg('Loading image for OCR...');
    setOcrLoading(true);
    setTrueText(item.medicines);
    setTitle(item.filename.replace('.jpg', '').replace('.png', ''));
    try {
      const imgRes = await fetch(item.image_url);
      const blob = await imgRes.blob();
      const file = new File([blob], item.filename, { type: blob.type });
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));

      const form = new FormData();
      form.append('image', file);
      const res = await postForm('/api/notes/ocr-preview', form);
      setOcrText(res.ocr_text || '');
      setMsg('OCR complete! Ground truth (medicines) pre-filled from dataset.');
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setOcrLoading(false);
    }
  };

  // ── Save note ───────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !trueText.trim()) {
      setMsg('Title and ground truth text are required.');
      return;
    }
    setSaving(true);
    setMsg('');
    const form = new FormData();
    form.append('title', title);
    form.append('true_text', trueText);
    if (ocrText) form.append('ocr_text', ocrText);
    if (trueTopic) form.append('true_topic', trueTopic);
    if (imageFile) form.append('image', imageFile);
    try {
      await postForm('/api/notes', form);
      setTitle(''); setTrueText(''); setOcrText(''); setTrueTopic('');
      setImageFile(null); setImagePreview(null);
      if (fileRef.current) fileRef.current.value = '';
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
      <h1 className="page-title">Upload</h1>
      <p className="page-subtitle">Upload a handwritten prescription image or pick one from the dataset</p>

      <div className="tab-bar" style={{ marginBottom: 20 }}>
        <button className={tab === 'upload' ? 'active' : ''} onClick={() => setTab('upload')}>
          Upload Image
        </button>
        <button className={tab === 'gallery' ? 'active' : ''} onClick={() => setTab('gallery')}>
          Dataset Gallery ({gallery.length})
        </button>
      </div>

      {/* ── Gallery Tab ─────────────────────────────────────────────────── */}
      {tab === 'gallery' && (
        <div className="chart-section">
          <h3>Handwritten Medical Records Dataset</h3>
          <p className="caption">Click an image to run OCR on it and add to your notes</p>
          <div className="gallery-grid">
            {gallery.map((item) => (
              <div key={item.filename} className="gallery-card" onClick={() => handleGallerySelect(item)}>
                <img src={item.image_url} alt={item.filename} loading="lazy" />
                <div className="gallery-label">
                  <span className="gallery-name">{item.filename}</span>
                  <span className="gallery-gt">{item.medicines}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Upload Tab ──────────────────────────────────────────────────── */}
      {tab === 'upload' && (
        <div className="two-col">
          <div className="chart-section">
            <h3>1. Select Image</h3>
            <div className="form-group">
              <label>Upload prescription image (JPG/PNG)</label>
              <input type="file" accept="image/*" ref={fileRef}
                     onChange={(e) => e.target.files[0] && handleImageSelect(e.target.files[0])}
                     style={{ color: '#c8d0e7' }} />
            </div>

            {imagePreview && (
              <div style={{ marginTop: 12 }}>
                <img src={imagePreview} alt="Preview"
                     style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 8, border: '1px solid #2e3250' }} />
              </div>
            )}

            {imagePreview && !ocrText && (
              <button className="btn" onClick={handleRunOCR} disabled={ocrLoading}
                      style={{ marginTop: 12 }}>
                {ocrLoading ? 'Running Tesseract OCR...' : 'Run OCR'}
              </button>
            )}

            {ocrLoading && <LoadingSpinner message="Running Tesseract OCR on image..." />}

            {ocrText && (
              <div style={{ marginTop: 16 }}>
                <h3>2. OCR Result</h3>
                <pre className="text-viewer" style={{ maxHeight: 250 }}>{ocrText}</pre>
              </div>
            )}
          </div>

          <div className="chart-section">
            <h3>{ocrText ? '3. Ground Truth + Save' : '2. Note Details'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Title *</label>
                <input value={title} onChange={(e) => setTitle(e.target.value)}
                       placeholder="e.g. Prescription #1" />
              </div>
              <div className="form-group">
                <label>Ground Truth Text * (what the image actually says)</label>
                <textarea value={trueText} onChange={(e) => setTrueText(e.target.value)}
                          placeholder="Type the correct text from the prescription..."
                          style={{ minHeight: 120 }} />
              </div>
              <div className="form-group">
                <label>Topic (optional)</label>
                <input value={trueTopic} onChange={(e) => setTrueTopic(e.target.value)}
                       placeholder="e.g. cardiology, general" />
              </div>
              <button className="btn" type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Note'}
              </button>
              {msg && <p style={{ marginTop: 10, color: msg.startsWith('Error') || msg.startsWith('OCR Error') ? '#e84c4c' : '#51cf66' }}>{msg}</p>}
            </form>
          </div>
        </div>
      )}

      {/* ── Existing Notes ──────────────────────────────────────────────── */}
      <hr />
      <div className="chart-section">
        <h3>Saved Notes ({notes.length})</h3>
        {notes.length === 0 ? (
          <p style={{ color: '#6b7599' }}>No notes yet. Upload an image or pick from the gallery above.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {notes.map((n) => (
              <div key={n.id} style={{
                background: '#161926', border: '1px solid #2e3250', borderRadius: 8, padding: 14,
                display: 'flex', gap: 14, alignItems: 'flex-start',
              }}>
                {n.has_image && (
                  <img src={`/api/notes/${n.id}/image`} alt=""
                       style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 6, border: '1px solid #2e3250' }} />
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>{n.title}</strong>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      {n.has_ocr && <span style={{ fontSize: 11, color: '#51cf66', background: '#1a3a1a', padding: '2px 8px', borderRadius: 4 }}>OCR</span>}
                      <button className="btn danger" style={{ padding: '4px 10px', fontSize: 12 }}
                              onClick={() => handleDelete(n.id)}>Delete</button>
                    </div>
                  </div>
                  <p style={{ color: '#6b7599', fontSize: 13, marginTop: 4 }}>
                    GT: {n.true_text?.slice(0, 100)}{n.true_text?.length > 100 ? '...' : ''}
                  </p>
                  {n.has_ocr && (
                    <p style={{ color: '#8b95b0', fontSize: 12, marginTop: 2 }}>
                      OCR: {n.ocr_text?.slice(0, 80)}{n.ocr_text?.length > 80 ? '...' : ''}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
