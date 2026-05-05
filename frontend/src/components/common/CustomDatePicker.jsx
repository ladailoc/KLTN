import { Calendar } from "lucide-react";

export function CustomDatePicker({
  value,
  onChange,
  placeholder = "DD/MM/YYYY",
}) {
  // Format from YYYY-MM-DD to DD/MM/YYYY
  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const [y, m, d] = dateStr.split("-");
    return `${d}/${m}/${y}`;
  };

  return (
    <div
      className="custom-date-picker"
      style={{ position: "relative", width: "100%" }}
    >
      {/* Visual trigger looking like CustomSelect */}
      <div
        className="select-trigger"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ color: value ? "var(--ink)" : "#94a3b8" }}>
          {value ? formatDate(value) : placeholder}
        </span>
        <Calendar size={16} color="#64748b" />
      </div>

      {/* Invisible native date input layered on top to catch clicks and open calendar */}
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          opacity: 0,
          cursor: "pointer",
        }}
      />
    </div>
  );
}
