import { useState, useEffect, useMemo } from 'react';
import { fetchJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import DataTable from '../components/DataTable';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  BarChart, Bar, Cell,
} from 'recharts';

const STAGE_COLORS = {
  original: '#51cf66',
  ocr_raw: '#4c9be8',
  spell_corrected: '#f0a500',
  summarized: '#e84c4c',
};

const METRIC_OPTIONS = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'f1', label: 'F1 Score' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
];

export default function Degradation() {
  const [data, setData] = useState(null);
  const [metric, setMetric] = useState('accuracy');
  const [selectedRate, setSelectedRate] = useState(null);

  useEffect(() => {
    fetchJson('/api/degradation').then(setData);
  }, []);

  const curveData = useMemo(() => {
    if (!data) return [];
    const { aggregated } = data;
    const rates = [...new Set(aggregated.map((r) => r.error_rate))].sort((a, b) => a - b);
    return rates.map((rate) => {
      const row = { error_rate: rate };
      aggregated
        .filter((r) => r.error_rate === rate)
        .forEach((r) => { row[r.stage] = +(r[`mean_${metric}`] * 100).toFixed(2); });
      return row;
    });
  }, [data, metric]);

  const stages = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.aggregated.map((r) => r.stage))];
  }, [data]);

  const snowballData = useMemo(() => {
    if (!data || !selectedRate) return [];
    return stages.map((stage) => {
      const row = data.aggregated.find(
        (r) => r.stage === stage && r.error_rate === selectedRate
      );
      return {
        stage,
        value: row ? +(row[`mean_${metric}`] * 100).toFixed(2) : 0,
        drop: row ? +((1 - row[`mean_${metric}`]) * 100).toFixed(2) : 0,
      };
    });
  }, [data, selectedRate, metric, stages]);

  if (!data) return <LoadingSpinner message="Loading degradation data..." />;

  const rates = [...new Set(data.aggregated.map((r) => r.error_rate))].sort((a, b) => a - b);
  if (!selectedRate && rates.length) setSelectedRate(rates[Math.floor(rates.length / 2)]);

  const tableColumns = [
    { key: 'stage', label: 'Stage' },
    { key: 'error_rate', label: 'Error Rate' },
    { key: 'mean_accuracy', label: 'Accuracy', format: (v) => (v * 100).toFixed(2) + '%' },
    { key: 'mean_f1', label: 'F1', format: (v) => (v * 100).toFixed(2) + '%' },
    { key: 'mean_precision', label: 'Precision', format: (v) => (v * 100).toFixed(2) + '%' },
    { key: 'mean_recall', label: 'Recall', format: (v) => (v * 100).toFixed(2) + '%' },
    { key: 'n_runs', label: 'Runs' },
  ];

  return (
    <>
      <h1 className="page-title">ClinBERT Degradation Study</h1>
      <p className="page-subtitle">
        How OCR errors degrade ClinBERT classification across pipeline stages
      </p>

      <div className="tab-bar">
        {METRIC_OPTIONS.map((m) => (
          <button key={m.key} className={metric === m.key ? 'active' : ''} onClick={() => setMetric(m.key)}>
            {m.label}
          </button>
        ))}
      </div>

      <div className="chart-section">
        <h3>{METRIC_OPTIONS.find((m) => m.key === metric).label} Degradation Curves</h3>
        <p className="caption">Each line represents a pipeline stage; X-axis is injected error rate</p>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={curveData}>
            <CartesianGrid stroke="#1e2130" />
            <XAxis dataKey="error_rate" stroke="#6b7599"
                   label={{ value: 'Error Rate', position: 'insideBottom', offset: -5, fill: '#6b7599' }} />
            <YAxis domain={[0, 100]} stroke="#6b7599"
                   label={{ value: `${metric} (%)`, angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                     formatter={(v) => `${v}%`} />
            <Legend />
            {stages.map((stage) => (
              <Line key={stage} type="monotone" dataKey={stage} name={stage.replace(/_/g, ' ')}
                    stroke={STAGE_COLORS[stage] || '#888'} strokeWidth={2} dot={{ r: 4 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Stage Snowball at Error Rate = {selectedRate}</h3>
        <p className="caption">Select an error rate to see how quality drops across stages</p>
        <div className="tab-bar">
          {rates.map((r) => (
            <button key={r} className={selectedRate === r ? 'active' : ''} onClick={() => setSelectedRate(r)}>
              {r}
            </button>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={snowballData}>
            <XAxis dataKey="stage" stroke="#6b7599" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} stroke="#6b7599" />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                     formatter={(v) => `${v}%`} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}
                 label={{ position: 'top', fill: '#c8d0e7', fontSize: 12, formatter: (v) => `${v}%` }}>
              {snowballData.map((d, i) => (
                <Cell key={i} fill={STAGE_COLORS[d.stage] || '#888'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Full Results Table</h3>
        <DataTable columns={tableColumns} data={data.aggregated} defaultSort="error_rate" />
      </div>
    </>
  );
}
