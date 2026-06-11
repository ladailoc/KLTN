import {
  Bell,
  Grid2X2,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: Grid2X2 },
  { key: "alerts", label: "Alerts", icon: Bell },
  { key: "drivers", label: "Drivers", icon: Users },
  { key: "settings", label: "Settings", icon: Settings },
];

export function Sidebar({ currentPage, setCurrentPage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <h1>Camera AI</h1>
          <p>Safety Monitoring</p>
        </div>
      </div>

      <nav className="nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              className={`nav-item ${currentPage === item.key ? "active" : ""}`}
              onClick={() => setCurrentPage(item.key)}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div style={{
        padding: "16px 22px",
        borderTop: "1px solid var(--line-soft)",
        fontSize: "11px",
        color: "var(--muted)",
        fontWeight: 500,
      }}>
        <div style={{ marginBottom: "2px", fontWeight: 700, color: "var(--ink)", fontSize: "12px" }}>
          Camera AI v1.0
        </div>
        Driver Behavior Detection System
      </div>
    </aside>
  );
}
