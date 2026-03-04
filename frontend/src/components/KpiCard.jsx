export default function KpiCard({ label, value, sub, snowball }) {
  return (
    <div className={`kpi-card${snowball ? ' snowball' : ''}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}
