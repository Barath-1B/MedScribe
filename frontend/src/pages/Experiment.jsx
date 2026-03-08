import { useState, useEffect } from 'react';
import { fetchJson, postJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import DataTable from '../components/DataTable';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line, CartesianGrid,
} from 'recharts';

const ERROR_RATES = [0, 0.02, 0.05, 0.10, 0.15, 0.20];

const STAGE_COLORS = {
  ocr:              '#e84c4c',
  spell_correction: '#51cf66',
  summarization:    '#339af0',
  classification:   '#fcc419',
};

const STAGE_LABELS = {
  ocr:              'OCR / Error Injection',
  spell_correction: 'Spell Correction',
  summarization:    'Summarization',
  classification:   'Classification',
};

export default function Experiment() {
  const [notes, setNotes] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selectedNotes, setSelectedNotes] = useState([]);
  const [selectedRates, setSelectedRates] = useState([0, 0.05, 0.10, 0.20]);
  const [errorType, setErrorType] = useState('mixed');
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState('');
  const [viewTab, setViewTab] = useState('cer');   // cer | snowball | table

  const loadData = () => {
    fetchJson('/api/notes').then(setNotes);
    fetchJson('/api/experiments').then(setExperiments);
  };

  useEffect(() => { loadData(); }, []);

  const toggleNote = (id) => {
    setSelectedNotes((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleRate = (r) => {
    setSelectedRates((prev) =>
      prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]
    );
  };

  const handleRun = async () => {
    if (!selectedNotes.length) { setMsg('Select at least one note.'); return; }
    if (!selectedRates.length) { setMsg('Select at least one error rate.'); return; }
    setRunning(true);
    setMsg('');
    try {
      const result = await postJson('/api/experiments/run', {
        note_ids: selectedNotes,
        error_rates: selectedRates,
        error_type: errorType,
      });
      setMsg(`Done! ${result.experiments?.length || 0} experiments completed.`);
      loadData();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  /* ── Chart data: CER at each stage per experiment ── */
  const completed = experiments.filter(
    (e) => e.status === 'completed' && e.stage_results?.length
  );

  const cerChartData = completed.map((e) => {
    const row = {
      label: `${e.note_title || 'Note'} @ ${(e.error_rate * 100).toFixed(0)}%`,
      mode: e.mode,
    };
    e.stage_results.forEach((s) => {
      if (s.cer != null) row[`${s.stage_name}_cer`] = +(s.cer.toFixed(2));
      if (s.wer != null) row[`${s.stage_name}_wer`] = +(s.wer.toFixed(2));
    });
    return row;
  });

  /* ── Snowball chart: CER progression through stages for each experiment ── */
  const STAGE_ORDER = ['ocr', 'spell_correction', 'summarization', 'classification'];

  const snowballData = STAGE_ORDER.map((stageName, idx) => {
    const point = { stage: STAGE_LABELS[stageName] || stageName, order: idx };
    completed.forEach((e) => {
      const sr = e.stage_results.find((s) => s.stage_name === stageName);
      const key = `${e.note_title || 'Note'} @ ${(e.error_rate * 100).toFixed(0)}%`;
      point[key] = sr?.cer != null ? +(sr.cer.toFixed(2)) : null;
    });
    return point;
  });

  const snowballKeys = completed.map(
    (e) => `${e.note_title || 'Note'} @ ${(e.error_rate * 100).toFixed(0)}%`
  );
  const lineColors = ['#e84c4c', '#51cf66', '#339af0', '#fcc419', '#cc5de8', '#ff922b', '#22b8cf', '#f06595'];

  /* ── Results table columns ── */
  const resultColumns = [
    { key: 'id', label: 'ID' },
    { key: 'note_title', label: 'Note' },
    { key: 'error_rate', label: 'Error Rate', format: (v) => `${(v * 100).toFixed(0)}%` },
    { key: 'error_type', label: 'Error Type' },
    { key: 'status', label: 'Status' },
    { key: 'mode', label: 'Mode', format: (v) => v === 'real_ocr' ? 'Real OCR' : 'Simulated' },
    { key: 'run_time_seconds', label: 'Time (s)', format: (v) => v?.toFixed(1) || '-' },
  ];

  const viewTabs = [
    { id: 'cer',      label: 'CER by Stage' },
    { id: 'snowball', label: 'Snowball' },
    { id: 'table',    label: 'Results Table' },
  ];

  return (
    <>
      <h1 className="page-title">Run Experiments</h1>
      <p className="page-subtitle">
        Run the 4-stage pipeline on your notes with different error rates to measure error snowballing
      </p>

      <div className="two-col">
        {/* ── LEFT: Configure ── */}
        <div className="chart-section">
          <h3>Configure Experiment</h3>

          <div className="form-group">
            <label>Select Notes</label>
            {notes.length === 0 ? (
              <p style={{ color: '#6b7599', fontSize: 13 }}>No notes available. Upload notes first.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {notes.map((n) => (
                  <label key={n.id} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', color: '#c8d0e7' }}>
                    <input type="checkbox" checked={selectedNotes.includes(n.id)}
                           onChange={() => toggleNote(n.id)} />
                    <span>{n.title}</span>
                    {n.has_ocr && (
                      <span style={{
                        fontSize: 10, background: '#1a5c2e', color: '#51cf66',
                        padding: '2px 6px', borderRadius: 4, marginLeft: 4,
                      }}>OCR</span>
                    )}
                    {n.has_image && (
                      <span style={{
                        fontSize: 10, background: '#1a3a5c', color: '#339af0',
                        padding: '2px 6px', borderRadius: 4, marginLeft: 2,
                      }}>IMG</span>
                    )}
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Error Rates</label>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {ERROR_RATES.map((r) => (
                <button key={r}
                        className={`tab-bar-btn ${selectedRates.includes(r) ? 'active' : ''}`}
                        onClick={() => toggleRate(r)}
                        style={{
                          background: selectedRates.includes(r) ? '#2e3250' : '#1e2130',
                          color: selectedRates.includes(r) ? '#f0f4ff' : '#8b95b0',
                          border: '1px solid #2e3250', borderRadius: 6, padding: '6px 12px',
                          cursor: 'pointer', fontSize: 13,
                        }}>
                  {(r * 100).toFixed(0)}%
                </button>
              ))}
            </div>
            <p style={{ color: '#6b7599', fontSize: 11, marginTop: 4 }}>
              0% = use real OCR text (if available) or clean ground truth
            </p>
          </div>

          <div className="form-group">
            <label>Error Type</label>
            <select value={errorType} onChange={(e) => setErrorType(e.target.value)}>
              <option value="mixed">Mixed (sub + del + ins)</option>
              <option value="substitution">Substitution only</option>
              <option value="deletion">Deletion only</option>
              <option value="insertion">Insertion only</option>
            </select>
          </div>

          <button className="btn" onClick={handleRun} disabled={running}>
            {running ? 'Running pipeline...' : `Run ${selectedNotes.length * selectedRates.length} Experiment(s)`}
          </button>
          {msg && <p style={{ marginTop: 10, color: msg.startsWith('Error') ? '#e84c4c' : '#51cf66' }}>{msg}</p>}
        </div>

        {/* ── RIGHT: Results ── */}
        <div className="chart-section">
          <h3>Experiment Results ({experiments.length})</h3>

          {experiments.length === 0 ? (
            <p style={{ color: '#6b7599' }}>No experiments run yet. Configure and run experiments on the left.</p>
          ) : (
            <>
              {/* View tabs */}
              <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
                {viewTabs.map((t) => (
                  <button key={t.id}
                          onClick={() => setViewTab(t.id)}
                          style={{
                            background: viewTab === t.id ? '#2e3250' : '#1e2130',
                            color: viewTab === t.id ? '#f0f4ff' : '#8b95b0',
                            border: '1px solid #2e3250', borderRadius: 6, padding: '6px 14px',
                            cursor: 'pointer', fontSize: 13,
                          }}>
                    {t.label}
                  </button>
                ))}
              </div>

              {/* CER by Stage bar chart */}
              {viewTab === 'cer' && cerChartData.length > 0 && (
                <>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={cerChartData}>
                      <XAxis dataKey="label" angle={-30} textAnchor="end" height={80}
                             tick={{ fontSize: 10 }} stroke="#6b7599" />
                      <YAxis stroke="#6b7599" label={{ value: 'CER %', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
                      <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
                      <Legend />
                      {Object.entries(STAGE_COLORS).map(([stage, color]) => (
                        <Bar key={stage} dataKey={`${stage}_cer`}
                             name={STAGE_LABELS[stage]} fill={color} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>

                  {/* Mode badges */}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                    {completed.map((e) => (
                      <span key={e.id} style={{
                        fontSize: 11, padding: '3px 8px', borderRadius: 4,
                        background: e.mode === 'real_ocr' ? '#1a5c2e' : '#3d2b1a',
                        color: e.mode === 'real_ocr' ? '#51cf66' : '#fcc419',
                      }}>
                        #{e.id} {e.mode === 'real_ocr' ? 'Real OCR' : 'Simulated'}
                      </span>
                    ))}
                  </div>
                </>
              )}

              {/* Snowball line chart: CER across stages */}
              {viewTab === 'snowball' && snowballData.length > 0 && (
                <>
                  <p style={{ color: '#6b7599', fontSize: 12, marginBottom: 8 }}>
                    CER at each pipeline stage — shows how errors propagate (snowball) through the pipeline
                  </p>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={snowballData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2e3250" />
                      <XAxis dataKey="stage" stroke="#6b7599" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#6b7599" label={{ value: 'CER %', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
                      <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
                      <Legend />
                      {snowballKeys.map((key, i) => (
                        <Line key={key} type="monotone" dataKey={key}
                              stroke={lineColors[i % lineColors.length]}
                              strokeWidth={2} dot={{ r: 4 }} connectNulls />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </>
              )}

              {/* Results table */}
              {viewTab === 'table' && (
                <>
                  <DataTable columns={resultColumns} data={experiments} defaultSort="id" />
                  <div style={{ marginTop: 12 }}>
                    <a href="/api/results/export/csv" className="btn"
                       style={{ textDecoration: 'none', display: 'inline-block' }}>
                      Export CSV
                    </a>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
