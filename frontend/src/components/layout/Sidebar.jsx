import {
  Bell,
  Grid2X2,
  MonitorDot,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: Grid2X2 },
  { key: "alerts", label: "Alerts", icon: Bell },
  { key: "devices", label: "Devices", icon: MonitorDot },
  { key: "drivers", label: "Drivers", icon: Users },
  { key: "settings", label: "Settings", icon: Settings },
];

export function Sidebar({ currentPage, setCurrentPage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={24} />
        </div>
        <div>
          <h1>Sentinel AI</h1>
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
              <Icon size={22} />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
