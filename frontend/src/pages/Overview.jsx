import { useState, useEffect } from 'react';
import { fetchJson } from '../api';
import KpiCard from '../components/KpiCard';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  ScatterChart, Scatter, CartesianGrid, Line, ComposedChart, Legend,
} from 'recharts';

const CASCADE_COLORS = ['#4c9be8', '#f0a500', '#e87c4c', '#e84c4c', '#9b1b1b'];

export default function Overview() {
  const [data, setData] = useState(null);
  const [docs, setDocs] = useState(null);

  useEffect(() => {
    fetchJson('/api/analysis/overview').then(setData);
    fetchJson('/api/analysis').then((r) => setDocs(r.documents));
  }, []);

  if (!data || !docs) return <LoadingSpinner message="Running OCR analysis on 50 documents..." />;

  const p = data.propagation;
  const cascade = [
    { name: 'Character', rate: p.char_error },
    { name: 'Word', rate: p.word_error },
    { name: 'Line (~8w)', rate: p.line_error },
    { name: 'Sentence (~20w)', rate: p.sentence_error },
    { name: 'Document (~200w)', rate: p.document_error },
  ];

  return (
    <>
      <h1 className="page-title">OCR Error Analysis — Clinical Texts</h1>
      <p className="page-subtitle">
        Dataset: FUNSD clinical forms | {data.total_documents} documents | Tesseract OCR
      </p>

      <div className="kpi-grid">
        <KpiCard label="Avg Character Error Rate" value={`${data.avg_cer}%`} sub="lower is better" />
        <KpiCard label="Avg Word Error Rate" value={`${data.avg_wer}%`} sub="lower is better" />
        <KpiCard label="Avg Accuracy (char)" value={`${data.avg_accuracy}%`} sub="higher is better" />
        <KpiCard label="Snowball Factor" value={`${data.snowball_factor}x`}
                 sub={`CER amplifies ${data.snowball_factor}x into WER`} snowball />
      </div>

      <div className="chart-section">
        <h3>Error Snowball Effect</h3>
        <p className="caption">
          A single character error corrupts an entire word. Word errors compound into lines,
          sentences, and documents.
        </p>
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={cascade}>
            <XAxis dataKey="name" stroke="#6b7599" />
            <YAxis domain={[0, 110]} stroke="#6b7599" />
            <Tooltip
              contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
              formatter={(v) => `${v.toFixed(1)}%`}
            />
            <Bar dataKey="rate" radius={[6, 6, 0, 0]} label={{ position: 'top', fill: '#c8d0e7', fontSize: 12, formatter: (v) => `${v.toFixed(1)}%` }}>
              {cascade.map((_, i) => <Cell key={i} fill={CASCADE_COLORS[i]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="two-col">
        <div className="info-box">
          <strong>What the snowball factor means:</strong><br /><br />
          At character level, {data.avg_cer}% of characters are wrong.<br /><br />
          At word level, {data.avg_wer}% of words are wrong — that's a{' '}
          <strong>{data.snowball_factor}x amplification</strong>. One bad character
          corrupts an entire word.<br /><br />
          By sentence level, an estimated <strong>{p.sentence_error}%</strong> of sentences
          contain at least one error.
        </div>
        <div className="info-box warning">
          <strong>Clinical impact:</strong><br /><br />
          With WER = {data.avg_wer}%, roughly 2 in 3 words in a clinical document are
          misread. In a medical context this could mean:<br />
          - Drug names read incorrectly<br />
          - Dosages or values corrupted<br />
          - Diagnoses misrepresented<br /><br />
          An estimated <strong>{p.document_error}%</strong> of documents contain at least one error.
        </div>
      </div>

      <hr />

      <div className="chart-section">
        <h3>CER vs WER Correlation</h3>
        <p className="caption">Each point is one document. Trend slope: {data.trend_slope}x</p>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart>
            <CartesianGrid stroke="#1e2130" />
            <XAxis dataKey="cer" type="number" name="CER" stroke="#6b7599"
                   label={{ value: 'CER (%)', position: 'insideBottom', offset: -5, fill: '#6b7599' }}
                   domain={[0, 'auto']} />
            <YAxis dataKey="wer" type="number" name="WER" stroke="#6b7599"
                   label={{ value: 'WER (%)', angle: -90, position: 'insideLeft', fill: '#6b7599' }}
                   domain={[0, 'auto']} />
            <Tooltip
              contentStyle={{ background: '#1e2130', border: '1px solid #2e3250', color: '#c8d0e7' }}
              formatter={(v) => `${v.toFixed(2)}%`}
            />
            <Scatter data={docs} fill="#4c9be8" />
            <Line data={[{ cer: 0, wer: 0 }, { cer: 100, wer: 100 }]}
                  dataKey="wer" stroke="#444" strokeDasharray="5 5"
                  dot={false} name="WER=CER" legendType="plainline" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
