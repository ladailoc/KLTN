export function ConfidenceBar({ value }) {
  const percent = Math.round(Number(value || 0) * 100);

  return (
    <div className="confidence-cell">
      <div className="confidence-track">
        <div
          className="confidence-fill"
          style={{ width: `${percent}%` }}
        />
      </div>
      <strong>{percent}%</strong>
    </div>
  );
}
