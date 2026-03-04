import { useState, useEffect, useMemo } from 'react';
import { fetchJson } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
  PieChart, Pie,
} from 'recharts';

const COLORS = ['#e84c4c', '#f0a500', '#4c9be8'];
const PIE_COLORS = ['#e84c4c', '#f0a500', '#4c9be8', '#51cf66', '#9b59b6', '#1abc9c'];

export default function ErrorBreakdown() {
  const [docs, setDocs] = useState(null);
  const [view, setView] = useState('char');

  useEffect(() => {
    fetchJson('/api/analysis').then((r) => setDocs(r.documents));
  }, []);

  const agg = useMemo(() => {
    if (!docs) return null;
    const totals = { sub: 0, del: 0, ins: 0 };
    const wTotals = { sub: 0, del: 0, ins: 0 };
    docs.forEach((d) => {
      totals.sub += d.cer_sub;
      totals.del += d.cer_del;
      totals.ins += d.cer_ins;
      wTotals.sub += d.wer_sub;
      wTotals.del += d.wer_del;
      wTotals.ins += d.wer_ins;
    });
    return { char: totals, word: wTotals };
  }, [docs]);

  if (!docs) return <LoadingSpinner message="Loading error breakdown..." />;

  const isChar = view === 'char';
  const prefix = isChar ? 'cer' : 'wer';

  const stackedData = docs.map((d) => ({
    filename: d.filename,
    Substitutions: d[`${prefix}_sub`],
    Deletions: d[`${prefix}_del`],
    Insertions: d[`${prefix}_ins`],
  }));

  const totals = isChar ? agg.char : agg.word;
  const total = totals.sub + totals.del + totals.ins;
  const pieData = [
    { name: 'Substitutions', value: totals.sub },
    { name: 'Deletions', value: totals.del },
    { name: 'Insertions', value: totals.ins },
  ];

  return (
    <>
      <h1 className="page-title">Error Type Breakdown</h1>
      <p className="page-subtitle">
        Substitutions, deletions, and insertions across {docs.length} documents
      </p>

      <div className="tab-bar">
        <button className={view === 'char' ? 'active' : ''} onClick={() => setView('char')}>Character Errors</button>
        <button className={view === 'word' ? 'active' : ''} onClick={() => setView('word')}>Word Errors</button>
      </div>

      <div className="two-col">
        <div className="chart-section">
          <h3>Aggregate Error Distribution</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                   innerRadius={60} outerRadius={110}
                   label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
            </PieChart>
          </ResponsiveContainer>
          <p className="caption">
            Total {isChar ? 'character' : 'word'} errors: {total} (Sub: {totals.sub}, Del: {totals.del}, Ins: {totals.ins})
          </p>
        </div>

        <div className="chart-section">
          <h3>Error Counts Summary</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={[
              { type: 'Substitutions', count: totals.sub },
              { type: 'Deletions', count: totals.del },
              { type: 'Insertions', count: totals.ins },
            ]}>
              <XAxis dataKey="type" stroke="#6b7599" />
              <YAxis stroke="#6b7599" />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}
                   label={{ position: 'top', fill: '#c8d0e7', fontSize: 12 }}>
                {COLORS.map((c, i) => <Cell key={i} fill={c} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Stacked Error Types per Document</h3>
        <ResponsiveContainer width="100%" height={420}>
          <BarChart data={stackedData}>
            <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 9 }} stroke="#6b7599" />
            <YAxis stroke="#6b7599" label={{ value: 'Error Count', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
            <Legend />
            <Bar dataKey="Substitutions" stackId="a" fill={COLORS[0]} />
            <Bar dataKey="Deletions" stackId="a" fill={COLORS[1]} />
            <Bar dataKey="Insertions" stackId="a" fill={COLORS[2]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="chart-section">
        <h3>Error Type Ratio per Document</h3>
        <p className="caption">Shows what fraction of each document's errors come from each type</p>
        <ResponsiveContainer width="100%" height={420}>
          <BarChart data={stackedData.map((d) => {
            const t = d.Substitutions + d.Deletions + d.Insertions || 1;
            return {
              filename: d.filename,
              Substitutions: +((d.Substitutions / t) * 100).toFixed(1),
              Deletions: +((d.Deletions / t) * 100).toFixed(1),
              Insertions: +((d.Insertions / t) * 100).toFixed(1),
            };
          })}>
            <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 9 }} stroke="#6b7599" />
            <YAxis domain={[0, 100]} stroke="#6b7599" label={{ value: '%', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
                     formatter={(v) => `${v}%`} />
            <Legend />
            <Bar dataKey="Substitutions" stackId="a" fill={COLORS[0]} />
            <Bar dataKey="Deletions" stackId="a" fill={COLORS[1]} />
            <Bar dataKey="Insertions" stackId="a" fill={COLORS[2]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
