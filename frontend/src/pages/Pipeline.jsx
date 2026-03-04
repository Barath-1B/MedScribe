import { useState, useEffect } from 'react';
import { fetchJson } from '../api';
import KpiCard from '../components/KpiCard';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
  PieChart, Pie,
} from 'recharts';

const STAGE_COLORS = ['#4c9be8', '#51cf66', '#f0a500', '#e84c4c'];
const PIE_COLORS = ['#4c9be8', '#51cf66', '#f0a500', '#e84c4c', '#9b59b6', '#1abc9c'];

export default function Pipeline() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchJson('/api/pipeline').then(setData);
  }, []);

  if (!data) return <LoadingSpinner message="Running full 4-stage pipeline..." />;

  const { results, averages } = data;

  const stageQuality = [
    { name: 'OCR Acc', value: +(100 - averages.s1_cer).toFixed(1) },
    { name: 'Post-Spell Acc', value: +(100 - averages.s2_cer).toFixed(1) },
    { name: 'ROUGE-1', value: +averages.s3_rouge1.toFixed(1) },
    { name: 'Topic Conf', value: +(averages.s4_confidence * 100).toFixed(1) },
  ];

  // Topic counts for pie
  const topicCounts = {};
  results.forEach((r) => { topicCounts[r.s4_topic] = (topicCounts[r.s4_topic] || 0) + 1; });
  const topicData = Object.entries(topicCounts).map(([name, value]) => ({ name, value }));

  const nImproved = results.filter((r) => r.s2_cer < r.s1_cer).length;
  const nWorse = results.filter((r) => r.s2_cer > r.s1_cer).length;
  const nSame = results.filter((r) => r.s2_cer === r.s1_cer).length;

  return (
    <>
      <h1 className="page-title">Full 4-Stage Pipeline</h1>
      <p className="page-subtitle">
        OCR &rarr; Spell Correction &rarr; Summarization &rarr; Topic Classification
      </p>

      <div className="chart-section">
        <h3>Average Quality at Each Stage</h3>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={stageQuality}>
            <XAxis dataKey="name" stroke="#6b7599" />
            <YAxis domain={[0, 115]} stroke="#6b7599" />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}
                 label={{ position: 'top', fill: '#c8d0e7', fontSize: 12, formatter: (v) => `${v}%` }}>
              {stageQuality.map((_, i) => <Cell key={i} fill={STAGE_COLORS[i]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="kpi-grid">
        <KpiCard label="S1 Avg CER" value={`${averages.s1_cer}%`} />
        <KpiCard label="S2 Avg CER" value={`${averages.s2_cer}%`}
                 sub={`${(averages.s2_cer - averages.s1_cer).toFixed(1)}% vs S1`} />
        <KpiCard label="S3 Avg ROUGE-1" value={`${averages.s3_rouge1}%`} />
        <KpiCard label="S4 Avg Confidence" value={`${(averages.s4_confidence * 100).toFixed(1)}%`} />
      </div>

      <hr />

      <div className="chart-section">
        <h3>CER Before vs After Spell Correction</h3>
        <p className="caption">
          {nImproved} improved, {nWorse} worse (over-correction), {nSame} unchanged
        </p>
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={results}>
            <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 10 }} stroke="#6b7599" />
            <YAxis stroke="#6b7599" label={{ value: 'CER (%)', angle: -90, position: 'insideLeft', fill: '#6b7599' }} />
            <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
            <Legend />
            <Bar dataKey="s1_cer" name="OCR CER" fill="#e84c4c" opacity={0.85} />
            <Bar dataKey="s2_cer" name="Post-Spell CER" fill="#51cf66" opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <hr />

      <div className="two-col">
        <div className="chart-section">
          <h3>ROUGE per Document</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={results}>
              <XAxis dataKey="filename" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 9 }} stroke="#6b7599" />
              <YAxis stroke="#6b7599" />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
              <Legend />
              <Bar dataKey="s3_rouge1" name="ROUGE-1" fill="#4c9be8" />
              <Bar dataKey="s3_rougel" name="ROUGE-L" fill="#f0a500" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-section">
          <h3>Predicted Topic Distribution</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie data={topicData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                   innerRadius={60} outerRadius={110} label>
                {topicData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
