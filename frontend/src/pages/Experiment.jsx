import { useState, useEffect } from 'react';
import { fetchJson, postJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import DataTable from '../components/DataTable';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const ERROR_RATES = [0, 0.05, 0.1, 0.15, 0.2, 0.3];

export default function Experiment() {
  const [notes, setNotes] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selectedNotes, setSelectedNotes] = useState([]);
  const [selectedRates, setSelectedRates] = useState([0, 0.1, 0.2]);
  const [errorType, setErrorType] = useState('mixed');
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState('');

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

  const chartData = experiments
    .filter((e) => e.status === 'completed' && e.stage_results?.length)
    .map((e) => {
      const row = { label: `${e.note_title || 'Note'} @ ${e.error_rate}` };
      e.stage_results.forEach((s) => {
        if (s.cer !== null) row[`${s.stage_name}_cer`] = +s.cer.toFixed(2);
      });
      return row;
    });

  const resultColumns = [
    { key: 'id', label: 'ID' },
    { key: 'note_title', label: 'Note' },
    { key: 'error_rate', label: 'Error Rate' },
    { key: 'error_type', label: 'Error Type' },
    { key: 'status', label: 'Status' },
    { key: 'run_time_seconds', label: 'Time (s)', format: (v) => v?.toFixed(1) || '-' },
  ];

  return (
    <>
      <h1 className="page-title">Run Experiments</h1>
      <p className="page-subtitle">
        Run the 4-stage pipeline on your notes with different error rates
      </p>

      <div className="two-col">
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
                    {n.title}
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

        <div className="chart-section">
          <h3>Experiment Results ({experiments.length})</h3>
          {experiments.length === 0 ? (
            <p style={{ color: '#6b7599' }}>No experiments run yet.</p>
          ) : (
            <>
              {chartData.length > 0 && (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <XAxis dataKey="label" angle={-30} textAnchor="end" height={80} tick={{ fontSize: 10 }} stroke="#6b7599" />
                    <YAxis stroke="#6b7599" />
                    <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
                    <Legend />
                    <Bar dataKey="error_injection_cer" name="After Injection" fill="#e84c4c" />
                    <Bar dataKey="spell_correction_cer" name="After Spell Fix" fill="#51cf66" />
                  </BarChart>
                </ResponsiveContainer>
              )}
              <div style={{ marginTop: 16 }}>
                <DataTable columns={resultColumns} data={experiments} defaultSort="id" />
              </div>
              <div style={{ marginTop: 12 }}>
                <a href="/api/results/export/csv" className="btn" style={{ textDecoration: 'none', display: 'inline-block' }}>
                  Export CSV
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
