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
        <Search size={16} />
        <input placeholder="Search alerts, device IDs, or event types..." />
      </div>

      <div className="header-right">
        <button
          className="header-icon-btn"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh data"
        >
          {loading ? (
            <Loader2 className="spin" size={17} />
          ) : (
            <RefreshCw size={17} />
          )}
        </button>

        <button className="header-icon-btn" title="Notifications">
          <Bell size={17} />
        </button>

        <button className="header-icon-btn" title="Help">
          <HelpCircle size={17} />
        </button>

        <div className={`backend-pill ${backendOnline ? "online" : "offline"}`}>
          <span />
          {backendOnline ? "Online" : "Offline"}
        </div>

        <span className="last-updated">{lastUpdated || "Not synced"}</span>

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
