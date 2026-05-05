export function StatCard({ label, value, icon: Icon, badge, colorClass }) {
  return (
    <div className="summary-card">
      <div className={`summary-icon ${colorClass || ""}`}>
        <Icon size={20} />
      </div>

      {badge && <span className="summary-badge">{badge}</span>}

      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
