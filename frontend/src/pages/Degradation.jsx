import { useState, useEffect, useMemo } from 'react';
import { fetchJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import DataTable from '../components/DataTable';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  BarChart, Bar, Cell,
} from 'recharts';

const STAGE_COLORS = {
  ocr: '#e84c4c',
  spell_correction: '#f0a500',
  summarization: '#4c9be8',
  classification: '#51cf66',
};

const METRIC_OPTIONS = [
  { key: 'cer', label: 'CER (%)' },
  { key: 'wer', label: 'WER (%)' },
  { key: 'recovery', label: 'Recovery (%)' },
];

export default function Degradation() {
  const [data, setData] = useState(null);
  const [metric, setMetric] = useState('cer');
  const [selectedRate, setSelectedRate] = useState(null);

  useEffect(() => {
    fetchJson('/api/degradation').then(setData);
  }, []);

  if (!data) return <LoadingSpinner message="Loading degradation data..." />;

  const { aggregated, error_rates, total_experiments } = data;

  if (!aggregated.length) {
    return (
      <>
        <h1 className="page-title">Snowball Degradation</h1>
        <div className="chart-section">
          <p style={{ color: '#6b7599', textAlign: 'center', padding: 40 }}>
            No experiment data yet. Go to the <strong>Experiment</strong> page to run
            pipeline experiments at different error rates, then come back here to see
            how errors snowball across stages.
          </p>
        </div>
      </>
    );
  }

  const rates = error_rates || [];
  if (!selectedRate && rates.length) setSelectedRate(rates[Math.floor(rates.length / 2)]);

  // Build curve data: error_rate on X, one line per stage
  const curveData = rates.map((rate) => {
    const row = { error_rate: (rate * 100).toFixed(0) + '%' };
    aggregated
      .filter((r) => r.error_rate === rate)
      .forEach((r) => {
        const val = r[`mean_${metric}`];
        if (val != null) row[r.stage] = val;
      });
    return row;
  });

  const stages = [...new Set(aggregated.map((r) => r.stage))];

  // Snowball at selected rate
  const snowballData = stages
    .filter((stage) => {
      const row = aggregated.find((r) => r.stage === stage && r.error_rate === selectedRate);
      return row && row[`mean_${metric}`] != null;
    })
    .map((stage) => {
      const row = aggregated.find((r) => r.stage === stage && r.error_rate === selectedRate);
      return {
        stage: stage.replace(/_/g, ' '),
        value: row[`mean_${metric}`] || 0,
        rawStage: stage,
      };
    });

  const tableColumns = [
    { key: 'stage', label: 'Stage' },
    { key: 'error_rate', label: 'Error Rate', format: (v) => (v * 100).toFixed(0) + '%' },
    { key: 'mean_cer', label: 'Avg CER', format: (v) => v != null ? v.toFixed(2) + '%' : '-' },
    { key: 'mean_wer', label: 'Avg WER', format: (v) => v != null ? v.toFixed(2) + '%' : '-' },
    { key: 'mean_recovery', label: 'Recovery', format: (v) => v != null ? v.toFixed(2) + '%' : '-' },
    { key: 'n_runs', label: 'Runs' },
  ];

  return (
    <>
      <h1 className="page-title">Snowball Degradation</h1>
      <p className="page-subtitle">
        How OCR errors cascade through each pipeline stage ({total_experiments} experiments)
      </p>

      <div className="tab-bar">
        {METRIC_OPTIONS.map((m) => (
          <button key={m.key} className={metric === m.key ? 'active' : ''} onClick={() => setMetric(m.key)}>
            {m.label}
          </button>
        ))}
      </div>

      <div className="chart-section">
        <h3>{METRIC_OPTIONS.find((m) => m.key === metric).label} Across Error Rates</h3>
        <p className="caption">Each line = a pipeline stage; X = injected error rate</p>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={curveData}>
            <CartesianGrid stroke="#1e2130" />
            <XAxis dataKey="error_rate" stroke="#6b7599" />
            <YAxis stroke="#6b7599"
                   label={{ value: metric.toUpperCase() + ' (%)', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                     formatter={(v) => `${v}%`} />
            <Legend />
            {stages.map((stage) => (
              <Line key={stage} type="monotone" dataKey={stage} name={stage.replace(/_/g, ' ')}
                    stroke={STAGE_COLORS[stage] || '#888'} strokeWidth={2} dot={{ r: 4 }}
                    connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Stage Snowball @ Error Rate = {selectedRate != null ? (selectedRate * 100).toFixed(0) + '%' : '?'}</h3>
        <p className="caption">Select an error rate to see how {metric.toUpperCase()} changes across stages</p>
        <div className="tab-bar">
          {rates.map((r) => (
            <button key={r} className={selectedRate === r ? 'active' : ''} onClick={() => setSelectedRate(r)}>
              {(r * 100).toFixed(0)}%
            </button>
          ))}
        </div>
        {snowballData.length > 0 ? (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={snowballData}>
              <XAxis dataKey="stage" stroke="#6b7599" tick={{ fontSize: 11 }} />
              <YAxis stroke="#6b7599" />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                       formatter={(v) => `${v}%`} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}
                   label={{ position: 'top', fill: '#c8d0e7', fontSize: 12 }}>
                {snowballData.map((d, i) => (
                  <Cell key={i} fill={STAGE_COLORS[d.rawStage] || '#888'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p style={{ color: '#6b7599', padding: 20 }}>No data for this metric at this error rate.</p>
        )}
      </div>

      <hr />

      <div className="chart-section">
        <h3>Full Results Table</h3>
        <DataTable columns={tableColumns} data={aggregated} defaultSort="error_rate" />
      </div>
    </>
  );
}
