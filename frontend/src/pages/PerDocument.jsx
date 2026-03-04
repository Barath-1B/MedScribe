import { useState, useEffect, useMemo } from 'react';
import { fetchJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import DataTable from '../components/DataTable';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

function colorScale(val, low = 0, high = 100) {
  const t = Math.min(1, Math.max(0, (val - low) / (high - low)));
  const r = Math.round(232 * t + 81 * (1 - t));
  const g = Math.round(76 * t + 207 * (1 - t));
  const b = Math.round(76 * t + 102 * (1 - t));
  return `rgb(${r},${g},${b})`;
}

export default function PerDocument() {
  const [docs, setDocs] = useState(null);
  const [sortBy, setSortBy] = useState('accuracy_desc');

  useEffect(() => {
    fetchJson('/api/analysis').then((r) => setDocs(r.documents));
  }, []);

  const sorted = useMemo(() => {
    if (!docs) return [];
    const d = [...docs];
    if (sortBy === 'accuracy_desc') d.sort((a, b) => b.accuracy - a.accuracy);
    else if (sortBy === 'accuracy_asc') d.sort((a, b) => a.accuracy - b.accuracy);
    else d.sort((a, b) => a.filename.localeCompare(b.filename));
    return d;
  }, [docs, sortBy]);

  if (!docs) return <LoadingSpinner message="Loading analysis..." />;

  const avgCer = docs.reduce((s, d) => s + d.cer, 0) / docs.length;
  const avgWer = docs.reduce((s, d) => s + d.wer, 0) / docs.length;

  const columns = [
    { key: 'filename', label: 'File' },
    { key: 'cer', label: 'CER %', format: (v) => v.toFixed(2) },
    { key: 'wer', label: 'WER %', format: (v) => v.toFixed(2) },
    { key: 'accuracy', label: 'Accuracy %', format: (v) => v.toFixed(2) },
    { key: 'cer_sub', label: 'Char Sub' },
    { key: 'cer_del', label: 'Char Del' },
    { key: 'cer_ins', label: 'Char Ins' },
    { key: 'wer_sub', label: 'Word Sub' },
    { key: 'wer_del', label: 'Word Del' },
    { key: 'wer_ins', label: 'Word Ins' },
  ];

  return (
    <>
      <h1 className="page-title">Per-Document Analysis</h1>
      <p className="page-subtitle">{docs.length} documents evaluated</p>

      <div className="tab-bar">
        <button className={sortBy === 'accuracy_desc' ? 'active' : ''} onClick={() => setSortBy('accuracy_desc')}>Best first</button>
        <button className={sortBy === 'accuracy_asc' ? 'active' : ''} onClick={() => setSortBy('accuracy_asc')}>Worst first</button>
        <button className={sortBy === 'filename' ? 'active' : ''} onClick={() => setSortBy('filename')}>File name</button>
      </div>

      <div className="chart-section">
        <h3>Accuracy per Document</h3>
        <ResponsiveContainer width="100%" height={Math.max(400, docs.length * 22)}>
          <BarChart data={sorted} layout="vertical">
            <XAxis type="number" domain={[0, 100]} stroke="#6b7599" />
            <YAxis dataKey="filename" type="category" width={180} tick={{ fontSize: 10 }} stroke="#6b7599" />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                     formatter={(v) => `${v.toFixed(1)}%`} />
            <Bar dataKey="accuracy" radius={[0, 6, 6, 0]}
                 label={{ position: 'right', fill: '#c8d0e7', fontSize: 10, formatter: (v) => `${v.toFixed(1)}%` }}>
              {sorted.map((d, i) => <Cell key={i} fill={colorScale(100 - d.accuracy)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="two-col">
        <div className="chart-section">
          <h3>CER per Document</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={sorted}>
              <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 9 }} stroke="#6b7599" />
              <YAxis stroke="#6b7599" />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
              <Bar dataKey="cer" fill="#4c9be8" radius={[4, 4, 0, 0]}>
                {sorted.map((d, i) => <Cell key={i} fill={colorScale(d.cer)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="caption">Avg CER: {avgCer.toFixed(1)}%</p>
        </div>

        <div className="chart-section">
          <h3>WER per Document</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={sorted}>
              <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 9 }} stroke="#6b7599" />
              <YAxis stroke="#6b7599" />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
              <Bar dataKey="wer" fill="#f0a500" radius={[4, 4, 0, 0]}>
                {sorted.map((d, i) => <Cell key={i} fill={colorScale(d.wer)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="caption">Avg WER: {avgWer.toFixed(1)}%</p>
        </div>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Full Results Table</h3>
        <DataTable columns={columns} data={sorted} defaultSort="accuracy" />
      </div>
    </>
  );
}
