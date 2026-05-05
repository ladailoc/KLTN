import {
  Bell,
  HelpCircle,
  Loader2,
  RefreshCw,
  Search,
} from "lucide-react";

export function Header({
  backendOnline,
  lastUpdated,
  onRefresh,
  loading,
  setCurrentPage,
}) {
  return (
    <header className="top-header">
      <div className="global-search">
        <Search size={18} />
        <input placeholder="Search alerts, device IDs, or event types..." />
      </div>

      <div className="header-right">
        <button
          className="header-icon-btn"
          onClick={onRefresh}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="spin" size={18} />
          ) : (
            <RefreshCw size={18} />
          )}
        </button>

        <button className="header-icon-btn">
          <Bell size={18} />
        </button>

        <button className="header-icon-btn">
          <HelpCircle size={18} />
        </button>

        <div className={`backend-pill ${backendOnline ? "online" : "offline"}`}>
          <span />
          Backend: {backendOnline ? "Online" : "Offline"}
        </div>

        <div className="last-updated">{lastUpdated || "Not synced"}</div>

        <div className="header-divider" />

        <div className="user-box" onClick={() => setCurrentPage("settings")}>
          <div className="user-text">
            <strong>System Operator</strong>
            <span>Administrator</span>
          </div>
          <div className="user-avatar">AI</div>
        </div>
      </div>
    </header>
  );
}
