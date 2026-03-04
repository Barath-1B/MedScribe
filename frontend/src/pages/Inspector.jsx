import { useState, useEffect } from 'react';
import { fetchJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import KpiCard from '../components/KpiCard';

export default function Inspector() {
  const [docs, setDocs] = useState(null);
  const [selected, setSelected] = useState(null);
  const [diff, setDiff] = useState(null);
  const [tab, setTab] = useState('ocr');

  useEffect(() => {
    fetchJson('/api/analysis/full').then((r) => {
      setDocs(r.documents);
      if (r.documents.length) setSelected(r.documents[0]);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setDiff(null);
    fetchJson(`/api/documents/${selected.filename}/diff`).then(setDiff);
  }, [selected]);

  if (!docs) return <LoadingSpinner message="Loading documents..." />;

  const imgUrl = selected ? `/api/documents/${selected.filename}/image` : null;

  return (
    <>
      <h1 className="page-title">Document Inspector</h1>
      <p className="page-subtitle">View OCR output, ground truth, and diff for each document</p>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: '#6b7599', marginRight: '0.5rem' }}>Select document:</label>
        <select
          value={selected?.filename || ''}
          onChange={(e) => setSelected(docs.find((d) => d.filename === e.target.value))}
          style={{
            background: '#1e2130', color: '#c8d0e7', border: '1px solid #2e3250',
            borderRadius: 6, padding: '0.4rem 0.8rem', fontSize: '0.9rem',
          }}
        >
          {docs.map((d) => (
            <option key={d.filename} value={d.filename}>{d.filename}</option>
          ))}
        </select>
      </div>

      {selected && (
        <>
          <div className="kpi-grid">
            <KpiCard label="CER" value={`${selected.cer.toFixed(2)}%`} />
            <KpiCard label="WER" value={`${selected.wer.toFixed(2)}%`} />
            <KpiCard label="Accuracy" value={`${selected.accuracy.toFixed(2)}%`} />
            <KpiCard label="Char Errors" value={`S:${selected.cer_sub} D:${selected.cer_del} I:${selected.cer_ins}`} />
          </div>

          <div className="two-col" style={{ marginTop: '1.5rem' }}>
            <div className="chart-section">
              <h3>Document Image</h3>
              {imgUrl ? (
                <img src={imgUrl} alt={selected.filename}
                     style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid #2e3250' }} />
              ) : (
                <p style={{ color: '#6b7599' }}>No image available</p>
              )}
            </div>

            <div className="chart-section">
              <div className="tab-bar">
                <button className={tab === 'ocr' ? 'active' : ''} onClick={() => setTab('ocr')}>OCR Text</button>
                <button className={tab === 'gt' ? 'active' : ''} onClick={() => setTab('gt')}>Ground Truth</button>
                <button className={tab === 'diff' ? 'active' : ''} onClick={() => setTab('diff')}>Diff View</button>
              </div>

              {tab === 'ocr' && (
                <pre className="text-viewer">{selected.ocr_text || 'No OCR text'}</pre>
              )}
              {tab === 'gt' && (
                <pre className="text-viewer">{selected.ground_truth || 'No ground truth'}</pre>
              )}
              {tab === 'diff' && (
                diff ? (
                  <div className="diff-viewer" dangerouslySetInnerHTML={{ __html: diff.diff_html }} />
                ) : (
                  <LoadingSpinner message="Generating diff..." />
                )
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
