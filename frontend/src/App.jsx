import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bell,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Cigarette,
  Download,
  Eye,
  Grid2X2,
  HardDrive,
  HelpCircle,
  Loader2,
  MonitorDot,
  Phone,
  RefreshCw,
  Search,
  Settings,
  Shield,
  ShieldCheck,
  Smartphone,
  Users,
  Video,
  X,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchAlerts,
  fetchHealth,
  fetchStatistics,
  getMediaUrl,
  manualReviewAlert,
  verifyAlert,
} from "./api";

const DEFAULT_LIMIT = 20;

const EVENT_META = {
  using_phone: {
    label: "Phone Use",
    apiLabel: "using_phone",
    icon: Phone,
    className: "event-phone",
    color: "#4f46e5",
  },
  smoking: {
    label: "Smoking",
    apiLabel: "smoking",
    icon: Cigarette,
    className: "event-smoking",
    color: "#e07800",
  },
  no_seatbelt: {
    label: "No Seatbelt",
    apiLabel: "no_seatbelt",
    icon: Shield,
    className: "event-seatbelt",
    color: "#c9181d",
  },
  unknown: {
    label: "Unknown",
    apiLabel: "unknown",
    icon: AlertTriangle,
    className: "event-unknown",
    color: "#bfc3cc",
  },
};

function getEventMeta(eventType) {
  return EVENT_META[eventType] || EVENT_META.unknown;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function formatConfidence(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function getEventCount(stats, eventType) {
  return (
    (stats?.by_event_type || []).find((item) => item.event_type === eventType)
      ?.count || 0
  );
}

function getTopDevice(stats) {
  const rows = stats?.by_device || [];
  if (!rows.length) return "-";
  return [...rows].sort(
    (a, b) => Number(b.count || 0) - Number(a.count || 0),
  )[0]?.source_device;
}

function buildPieData(stats) {
  const phone = getEventCount(stats, "using_phone");
  const smoking = getEventCount(stats, "smoking");
  const seatbelt = getEventCount(stats, "no_seatbelt");
  const known = phone + smoking + seatbelt;
  const total = stats?.total_alerts || known;
  const other = Math.max(0, total - known);

  return [
    { name: "using_phone", value: phone, color: EVENT_META.using_phone.color },
    { name: "smoking", value: smoking, color: EVENT_META.smoking.color },
    {
      name: "no_seatbelt",
      value: seatbelt,
      color: EVENT_META.no_seatbelt.color,
    },
    { name: "other", value: other, color: EVENT_META.unknown.color },
  ].filter((item) => item.value > 0);
}

function buildDeviceData(stats) {
  return (stats?.by_device || []).map((item) => ({
    name: item.source_device || "unknown",
    alerts: item.count || 0,
  }));
}

function buildTrendData(alerts) {
  const fallback = [
    { time: "00:00", alerts: 2 },
    { time: "03:00", alerts: 3 },
    { time: "06:00", alerts: 6 },
    { time: "09:00", alerts: 4 },
    { time: "12:00", alerts: 2 },
    { time: "15:00", alerts: 3 },
    { time: "18:00", alerts: 5 },
    { time: "21:00", alerts: 2 },
  ];

  if (!alerts?.length) return fallback;

  return fallback.map((item, index) => ({
    ...item,
    alerts: Math.max(1, Math.round(alerts.length / 3) + (index % 3)),
  }));
}

function Sidebar({ currentPage, setCurrentPage }) {
  const items = [
    { key: "dashboard", label: "Dashboard", icon: Grid2X2 },
    { key: "alerts", label: "Alerts", icon: Bell },
    { key: "devices", label: "Devices", icon: MonitorDot },
    { key: "drivers", label: "Drivers", icon: Users },
    { key: "settings", label: "Settings", icon: Settings },
  ];

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
        {items.map((item) => {
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

function Header({
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

function StatCard({ label, value, icon: Icon, badge, colorClass }) {
  return (
    <div className="summary-card">
      <div className={`summary-icon ${colorClass || ""}`}>
        <Icon size={22} />
      </div>

      {badge && <span className="summary-badge">{badge}</span>}

      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DashboardPage({
  stats,
  alerts,
  backendOnline,
  lastUpdated,
  setCurrentPage,
}) {
  const total = stats?.total_alerts || 0;
  const verified = stats?.verified_count || 0;
  const verifiedRate =
    total > 0 ? ((verified / total) * 100).toFixed(1) : "0.0";

  const phoneCount = getEventCount(stats, "using_phone");
  const smokingCount = getEventCount(stats, "smoking");
  const seatbeltCount = getEventCount(stats, "no_seatbelt");

  const pieData = buildPieData(stats);
  const deviceData = buildDeviceData(stats);
  const trendData = buildTrendData(alerts);

  return (
    <div className="page">
      <section className="page-header">
        <div>
          <h1>Dashboard Overview</h1>
          <p>Real-time monitoring summary for driver behavior alerts.</p>
        </div>

        <button
          className="primary-btn"
          onClick={() => setCurrentPage("alerts")}
        >
          View Alert Center
        </button>
      </section>

      <section className="summary-grid three">
        <StatCard
          label="Total Alerts"
          value={formatNumber(total)}
          icon={AlertTriangle}
          badge="+12% vs last 24h"
          colorClass="danger"
        />
        <StatCard
          label="Verified Rate"
          value={`${verifiedRate}%`}
          icon={ShieldCheck}
          badge="Optimal"
          colorClass="purple"
        />
        <StatCard
          label="Active Edge Devices"
          value={formatNumber((stats?.by_device || []).length)}
          icon={HardDrive}
          badge={backendOnline ? "All Systems Up" : "Backend Offline"}
          colorClass="gray"
        />
      </section>

      <section className="summary-grid six">
        <StatCard
          label="Using Phone"
          value={formatNumber(phoneCount)}
          icon={Smartphone}
          colorClass="blue"
        />
        <StatCard
          label="Smoking"
          value={formatNumber(smokingCount)}
          icon={Cigarette}
          colorClass="orange"
        />
        <StatCard
          label="No Seatbelt"
          value={formatNumber(seatbeltCount)}
          icon={Shield}
          colorClass="red"
        />
        <StatCard
          label="Verified"
          value={formatNumber(verified)}
          icon={CheckCircle2}
          colorClass="green"
        />
        <StatCard
          label="Pending"
          value={formatNumber(stats?.unverified_count || 0)}
          icon={CalendarClock}
          colorClass="gray"
        />
        <StatCard
          label="Latest Edge"
          value={getTopDevice(stats) || "-"}
          icon={MonitorDot}
          colorClass="blue"
        />
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <div className="panel-title">
            <h2>Alert Trends (24h)</h2>
            <span>Real-time sampling every 10m</span>
          </div>

          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trendData}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="alerts" fill="#dce3ee" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <div className="panel-title">
            <h2>Event Distribution</h2>
          </div>

          <div className="distribution-layout">
            <div className="donut-mini">
              <ResponsiveContainer width="100%" height={230}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    innerRadius={60}
                    outerRadius={88}
                    paddingAngle={3}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              <div className="donut-mini-center">
                <strong>{formatNumber(total)}</strong>
                <span>Total Events</span>
              </div>
            </div>

            <div className="event-list">
              {pieData.length === 0 ? (
                <p className="empty-text">No event data</p>
              ) : (
                pieData.map((item) => {
                  const percent =
                    total > 0 ? Math.round((item.value / total) * 100) : 0;
                  return (
                    <div className="event-line" key={item.name}>
                      <span style={{ background: item.color }} />
                      <div>
                        <strong>{item.name}</strong>
                        <small>
                          {item.value} events ({percent}%)
                        </small>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-grid lower">
        <div className="panel">
          <div className="panel-title">
            <h2>Alerts by Device</h2>
            <span>Latest sync: {lastUpdated || "-"}</span>
          </div>

          {deviceData.length === 0 ? (
            <div className="empty-box">No device statistics available</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={deviceData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="alerts" fill="#071226" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="panel risk-panel">
          <div className="panel-title">
            <h2>Risk Notifications</h2>
          </div>

          <div className="risk-item red">
            <AlertTriangle size={18} />
            <div>
              <strong>High Phone Usage</strong>
              <span>{phoneCount} phone-related alerts detected.</span>
            </div>
          </div>

          <div className="risk-item amber">
            <CalendarClock size={18} />
            <div>
              <strong>Manual Review Required</strong>
              <span>
                {stats?.unverified_count || 0} alerts are still pending.
              </span>
            </div>
          </div>

          <div className="risk-item blue">
            <ShieldCheck size={18} />
            <div>
              <strong>Cloud Verification</strong>
              <span>Use SlowFast only for suspicious clips.</span>
            </div>
          </div>

          <button className="link-btn" onClick={() => setCurrentPage("alerts")}>
            View All Alerts <ChevronRight size={16} />
          </button>
        </div>
      </section>
    </div>
  );
}

function EventBadge({ eventType }) {
  const meta = getEventMeta(eventType);
  const Icon = meta.icon;

  return (
    <span className={`event-badge ${meta.className}`}>
      <Icon size={14} />
      {meta.label}
    </span>
  );
}

function StatusBadge({ verified, reviewStatus }) {
  if (reviewStatus === "verified" || verified) {
    return <span className="status-badge verified">VERIFIED</span>;
  }

  if (reviewStatus === "rejected") {
    return <span className="status-badge rejected">REJECTED</span>;
  }

  if (reviewStatus === "unconfirmed") {
    return <span className="status-badge unconfirmed">UNCONFIRMED</span>;
  }

  return <span className="status-badge pending">PENDING</span>;
}

function ConfidenceBar({ value }) {
  const percent = Math.round(Number(value || 0) * 100);

  return (
    <div className="confidence-cell">
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${percent}%` }} />
      </div>
      <strong>{percent}%</strong>
    </div>
  );
}

function AlertsPage({
  alerts,
  total,
  totalPages,
  page,
  setPage,
  limit,
  setLimit,
  eventType,
  setEventType,
  device,
  setDevice,
  verified,
  setVerified,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  onApply,
  onReset,
  onOpenAlert,
  onVerify,
}) {
  return (
    <div className="page">
      <section className="page-header">
        <div>
          <h1>Alerts Center</h1>
          <p>
            Review driver behavior alerts, evidence clips, and Cloud
            verification results.
          </p>
        </div>

        <button className="secondary-btn" onClick={() => exportRows(alerts)}>
          <Download size={16} />
          Export CSV
        </button>
      </section>

      <section className="filter-panel">
        <label>
          <span>EVENT TYPE</span>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="using_phone">Using Phone</option>
            <option value="smoking">Smoking</option>
            <option value="no_seatbelt">No Seatbelt</option>
          </select>
        </label>

        <label>
          <span>DEVICE ID</span>
          <input
            value={device}
            onChange={(e) => setDevice(e.target.value)}
            placeholder="All Devices"
          />
        </label>

        <label>
          <span>STATUS</span>
          <select
            value={verified}
            onChange={(e) => setVerified(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="true">Verified</option>
            <option value="false">Pending</option>
          </select>
        </label>

        <label>
          <span>START DATE</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>

        <label>
          <span>END DATE</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>

        <label>
          <span>ROWS</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>

        <button className="apply-btn" onClick={onApply}>
          Apply
        </button>
        <button className="reset-btn" onClick={onReset}>
          Reset
        </button>
      </section>

      <section className="table-card">
        <div className="table-card-header">
          <h2>Recent Alerts</h2>
          <span>Total: {formatNumber(total)} records</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ALERT ID</th>
                <th>TIMESTAMP</th>
                <th>TYPE</th>
                <th>CONFIDENCE</th>
                <th>DEVICE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-row">
                    No alerts found
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="alert-id">
                      #AL-{String(alert.id).padStart(5, "0")}
                    </td>
                    <td>{alert.timestamp || "-"}</td>
                    <td>
                      <EventBadge eventType={alert.event_type} />
                    </td>
                    <td>
                      <ConfidenceBar value={alert.confidence} />
                    </td>
                    <td>{alert.source_device || "-"}</td>
                    <td>
                      <StatusBadge
                        verified={alert.verified}
                        reviewStatus={alert.review_status}
                      />
                    </td>
                    <td>
                      <div className="row-actions">
                        <button onClick={() => onOpenAlert(alert)}>
                          <Eye size={15} /> View
                        </button>
                        <button
                          className="verify-small"
                          onClick={() => onVerify(alert.id)}
                          disabled={!alert.clip_url}
                        >
                          Verify
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="pagination">
          <span>
            Showing page {page} of {totalPages}
          </span>
          <div className="pager">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
            >
              Previous
            </button>
            <strong>{page}</strong>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function DevicesPage({ stats, alerts }) {
  const devices = (stats?.by_device || []).map((item) => {
    const latest = alerts.find((a) => a.source_device === item.source_device);

    return {
      id: item.source_device,
      alerts: item.count,
      status: "Online",
      lastSync: latest?.timestamp || "-",
      location: "Cabin Camera",
    };
  });

  return (
    <div className="page">
      <section className="page-header">
        <div>
          <h1>Devices Management</h1>
          <p>
            Monitor Edge AI devices, camera streams, and synchronization status.
          </p>
        </div>
        <button className="primary-btn">+ Add Device</button>
      </section>

      <section className="device-grid">
        {devices.length === 0 ? (
          <div className="empty-box">No edge device data available.</div>
        ) : (
          devices.map((device) => (
            <div className="device-card" key={device.id}>
              <div className="device-card-top">
                <div className="device-icon">
                  <MonitorDot size={24} />
                </div>
                <span className="device-status online">{device.status}</span>
              </div>

              <h3>{device.id}</h3>
              <p>{device.location}</p>

              <div className="device-meta">
                <span>Total Alerts</span>
                <strong>{device.alerts}</strong>
              </div>

              <div className="device-meta">
                <span>Last Sync</span>
                <strong>{device.lastSync}</strong>
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  );
}

function DriversPage() {
  const drivers = [
    {
      name: "Alex Richardson",
      id: "DR-99231",
      license: "L33290-01A",
      score: 94,
      violations: "0 Active",
      level: "good",
      fleet: "Midwest Fleet",
    },
    {
      name: "Elena Rodriguez",
      id: "DR-88412",
      license: "P88210-99X",
      score: 78,
      violations: "2 Minor",
      level: "warning",
      fleet: "Northeast Fleet",
    },
    {
      name: "Marcus Chen",
      id: "DR-77102",
      license: "K01239-22B",
      score: 42,
      violations: "5 Critical",
      level: "danger",
      fleet: "Western Fleet",
    },
    {
      name: "Jordan Smith",
      id: "DR-66255",
      license: "M11002-88C",
      score: 91,
      violations: "1 Alert",
      level: "good",
      fleet: "Midwest Fleet",
    },
  ];

  return (
    <div className="page">
      <section className="page-header">
        <div>
          <h1>Drivers Management</h1>
          <p>
            Monitor driver performance, safety scores, and violation history
            across your fleet.
          </p>
        </div>

        <div className="page-actions">
          <button className="secondary-btn">
            <Download size={16} /> Export Data
          </button>
          <button className="primary-btn">+ Add New Driver</button>
        </div>
      </section>

      <section className="driver-filters">
        <label>
          <span>Search Driver</span>
          <div className="input-with-icon">
            <Search size={16} />
            <input placeholder="Name, ID, or License..." />
          </div>
        </label>

        <label>
          <span>Fleet Selection</span>
          <select>
            <option>All Fleets</option>
            <option>Midwest Fleet</option>
            <option>Northeast Fleet</option>
            <option>Western Fleet</option>
          </select>
        </label>

        <label>
          <span>Score Range</span>
          <div className="score-range">
            <input placeholder="0" />
            <span>-</span>
            <input placeholder="100" />
          </div>
        </label>
      </section>

      <section className="table-card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Driver Profile</th>
                <th>Employee ID</th>
                <th>License No.</th>
                <th>Safety Score</th>
                <th>Total Violations</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {drivers.map((driver) => (
                <tr key={driver.id}>
                  <td>
                    <div className="driver-profile">
                      <div className="driver-avatar">
                        {driver.name
                          .split(" ")
                          .map((x) => x[0])
                          .join("")}
                      </div>
                      <div>
                        <strong>{driver.name}</strong>
                        <span>Active • {driver.fleet}</span>
                      </div>
                    </div>
                  </td>
                  <td>{driver.id}</td>
                  <td>{driver.license}</td>
                  <td>
                    <div className="score-cell">
                      <div className="score-track">
                        <div
                          className={`score-fill ${driver.level}`}
                          style={{ width: `${driver.score}%` }}
                        />
                      </div>
                      <strong className={driver.level}>{driver.score}</strong>
                    </div>
                  </td>
                  <td>
                    <span className={`violation-pill ${driver.level}`}>
                      {driver.violations}
                    </span>
                  </td>
                  <td>
                    <ChevronRight size={18} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="dashboard-grid lower">
        <div className="panel">
          <div className="panel-title">
            <h2>Fleet Safety Overview</h2>
            <span>Weekly</span>
          </div>

          <ResponsiveContainer width="100%" height={240}>
            <BarChart
              data={[
                { day: "Mon", score: 88 },
                { day: "Tue", score: 82 },
                { day: "Wed", score: 90 },
                { day: "Thu", score: 86 },
                { day: "Fri", score: 78 },
                { day: "Sat", score: 92 },
                { day: "Sun", score: 85 },
              ]}
            >
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#071226" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel risk-panel">
          <div className="panel-title">
            <h2>Risk Notifications</h2>
          </div>

          <div className="risk-item red">
            <AlertTriangle size={18} />
            <div>
              <strong>Critical Score Drop</strong>
              <span>Marcus Chen's score dropped 12%.</span>
            </div>
          </div>

          <div className="risk-item amber">
            <CalendarClock size={18} />
            <div>
              <strong>License Expiring</strong>
              <span>Elena Rodriguez's license expires soon.</span>
            </div>
          </div>

          <div className="risk-item blue">
            <ShieldCheck size={18} />
            <div>
              <strong>Top Performer</strong>
              <span>Alex Richardson reached a safety milestone.</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="page">
      <section className="page-header">
        <div>
          <h1>Settings</h1>
          <p>
            Configure dashboard behavior, Cloud verification, and monitoring
            preferences.
          </p>
        </div>
      </section>

      <section className="settings-grid">
        <div className="panel settings-card">
          <h2>System Preferences</h2>

          <label>
            <span>Auto Refresh</span>
            <select>
              <option>Every 5 seconds</option>
              <option>Every 10 seconds</option>
              <option>Manual</option>
            </select>
          </label>

          <label>
            <span>Default Page Size</span>
            <select>
              <option>20 rows</option>
              <option>50 rows</option>
              <option>100 rows</option>
            </select>
          </label>

          <label>
            <span>Dashboard Theme</span>
            <select>
              <option>Light Monitoring</option>
              <option>Dark Command Center</option>
            </select>
          </label>
        </div>

        <div className="panel settings-card">
          <h2>Cloud Verification</h2>

          <label>
            <span>SlowFast Mode</span>
            <select>
              <option>Manual verification</option>
              <option>Auto verification</option>
            </select>
          </label>

          <label>
            <span>Unconfirmed Behavior</span>
            <select>
              <option>Human review required</option>
              <option>Keep as pending</option>
            </select>
          </label>

          <button className="primary-btn">Save Settings</button>
        </div>
      </section>
    </div>
  );
}

function EvidenceModal({
  alert,
  verificationResult,
  onClose,
  onVerify,
  onManualReview,
  verifying,
}) {
  const [reviewerNotes, setReviewerNotes] = useState("");

  if (!alert) return null;

  const frameUrl = getMediaUrl(alert.frame_url);
  const clipUrl = getMediaUrl(alert.clip_url);
  const eventJsonUrl = getMediaUrl(alert.event_json_url);
  const meta = getEventMeta(alert.event_type);

  return (
    <div className="modal-backdrop">
      <div className="alert-modal">
        <div className="modal-top">
          <div>
            <h2>Alert Details (ID #EV-{String(alert.id).padStart(3, "0")})</h2>
            <div className="modal-subline">
              <span className={`modal-event-pill ${meta.className}`}>
                {meta.label}
              </span>
              <span>Timestamp: {alert.timestamp || "-"}</span>
            </div>
          </div>

          <button className="close-btn" onClick={onClose}>
            <X size={26} />
          </button>
        </div>

        <div className="modal-body">
          <div className="evidence-column">
            <div className="video-box">
              {clipUrl ? (
                <video src={clipUrl} controls poster={frameUrl || undefined} />
              ) : frameUrl ? (
                <img src={frameUrl} alt="Evidence frame" />
              ) : (
                <div className="no-evidence">
                  <Video size={42} />
                  <span>No evidence available</span>
                </div>
              )}
            </div>

            {eventJsonUrl && (
              <a
                className="json-link"
                href={eventJsonUrl}
                target="_blank"
                rel="noreferrer"
              >
                View JSON Event
              </a>
            )}

            <button
              className="slowfast-btn"
              onClick={() => onVerify(alert.id)}
              disabled={!clipUrl || verifying}
            >
              {verifying ? (
                <Loader2 className="spin" size={22} />
              ) : (
                <Zap size={22} />
              )}
              {verifying ? "Verifying..." : "Verify with SlowFast AI"}
            </button>
          </div>

          <div className="metadata-column">
            <div className="metadata-card">
              <h3>TECHNICAL METADATA</h3>
              <div className="meta-row">
                <span>Alert ID</span>
                <strong>#EV-{String(alert.id).padStart(3, "0")}</strong>
              </div>
              <div className="meta-row">
                <span>Source Device</span>
                <strong>{alert.source_device || "-"}</strong>
              </div>
              <div className="meta-row">
                <span>AI Confidence</span>
                <strong>{formatConfidence(alert.confidence)}</strong>
              </div>
              <div className="meta-row">
                <span>Frame Index</span>
                <strong>{alert.frame_index ?? "-"}</strong>
              </div>
              <div className="meta-row">
                <span>Status</span>
                <strong>
                  {alert.review_status ||
                    (alert.verified ? "verified" : "pending")}
                </strong>
              </div>
            </div>

            <div className="reviewer-card">
              <h3>REVIEWER NOTES</h3>
              <textarea
                value={reviewerNotes}
                onChange={(e) => setReviewerNotes(e.target.value)}
                placeholder="Enter observation details..."
              />
            </div>
          </div>
        </div>

        <div className="verification-card">
          <div className="verify-title">
            <ShieldCheck size={22} />
            <h3>SlowFast Verification Result</h3>
          </div>

          {verificationResult ? (
            <div className="verify-grid">
              <div>
                <span>STATUS</span>
                <strong
                  className={
                    verificationResult.verified
                      ? "verified-text"
                      : "unconfirmed-text"
                  }
                >
                  {verificationResult.verified ? "VERIFIED" : "UNCONFIRMED"}
                </strong>
              </div>

              <div>
                <span>PREDICTED EVENT</span>
                <strong>
                  {verificationResult.predicted_project_event || "-"}
                </strong>
              </div>

              <div>
                <span>PREDICTED SCORE</span>
                <strong>
                  {verificationResult.predicted_project_score ?? "-"}
                </strong>
              </div>

              <div>
                <span>TOP-K LABELS</span>
                <div className="topk-list">
                  {(verificationResult.top_k || [])
                    .slice(0, 4)
                    .map((item, index) => (
                      <em key={`${item.label}-${index}`}>
                        {item.label} (
                        {Math.round(Number(item.score || 0) * 100)}%)
                      </em>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="verify-empty">
              Chưa có kết quả xác thực. Có thể chạy SlowFast hoặc xác thực thủ
              công.
            </p>
          )}
        </div>

        <div className="modal-footer">
          <button
            className="outline-btn danger-outline"
            onClick={() =>
              onManualReview(alert.id, {
                verified: false,
                review_status: "rejected",
                reviewer_notes: reviewerNotes,
                verified_by: "admin",
              })
            }
          >
            Mark False Positive
          </button>

          <button
            className="outline-btn"
            onClick={() =>
              onManualReview(alert.id, {
                verified: false,
                review_status: "unconfirmed",
                reviewer_notes: reviewerNotes,
                verified_by: "admin",
              })
            }
          >
            Save as Unconfirmed
          </button>

          <button
            className="confirm-btn"
            onClick={() =>
              onManualReview(alert.id, {
                verified: true,
                review_status: "verified",
                reviewer_notes: reviewerNotes,
                verified_by: "admin",
              })
            }
          >
            Confirm Alert
          </button>
        </div>
      </div>
    </div>
  );
}

function exportRows(rows) {
  if (!rows.length) {
    alert("Không có dữ liệu để export");
    return;
  }

  const headers = [
    "id",
    "timestamp",
    "event_type",
    "confidence",
    "frame_index",
    "source_device",
    "verified",
    "review_status",
    "notes",
  ];

  const csvRows = [
    headers.join(","),
    ...rows.map((row) =>
      headers
        .map((key) => `"${String(row[key] ?? "").replaceAll('"', '""')}"`)
        .join(","),
    ),
  ];

  const blob = new Blob([csvRows.join("\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "alerts_export.csv";
  a.click();

  URL.revokeObjectURL(url);
}

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const [backendOnline, setBackendOnline] = useState(false);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [eventType, setEventType] = useState("");
  const [device, setDevice] = useState("");
  const [verified, setVerified] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const [selectedAlert, setSelectedAlert] = useState(null);
  const [verificationResults, setVerificationResults] = useState({});
  const [verifyingId, setVerifyingId] = useState(null);

  const skip = useMemo(() => (page - 1) * limit, [page, limit]);

  async function loadData() {
    setLoading(true);
    setErrorMessage("");

    try {
      await fetchHealth();
      setBackendOnline(true);

      const params = {
        skip,
        limit,
        event_type: eventType,
        device,
        verified,
        start_date: startDate,
        end_date: endDate ? `${endDate}T23:59:59` : "",
      };

      const [statsData, alertsData] = await Promise.all([
        fetchStatistics(),
        fetchAlerts(params),
      ]);

      setStats(statsData);
      setAlerts(alertsData.items || []);
      setTotal(alertsData.total || 0);
      setTotalPages(alertsData.total_pages || 1);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      setBackendOnline(false);
      setErrorMessage(error.message || "Failed to fetch");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(alertId) {
    setVerifyingId(alertId);
    setErrorMessage("");

    try {
      const result = await verifyAlert(alertId);
      setVerificationResults((prev) => ({ ...prev, [alertId]: result }));
      await loadData();
    } catch (error) {
      setErrorMessage(error.message || "Verify failed");
    } finally {
      setVerifyingId(null);
    }
  }

  async function handleManualReview(alertId, payload) {
    setLoading(true);
    setErrorMessage("");

    try {
      await manualReviewAlert(alertId, payload);
      await loadData();
      setSelectedAlert(null);
    } catch (error) {
      setErrorMessage(error.message || "Manual review failed");
    } finally {
      setLoading(false);
    }
  }

  function resetFilters() {
    setEventType("");
    setDevice("");
    setVerified("");
    setStartDate("");
    setEndDate("");
    setLimit(DEFAULT_LIMIT);
    setPage(1);
  }

  useEffect(() => {
    loadData();
  }, [page, limit]);

  useEffect(() => {
    const timer = setInterval(loadData, 5000);
    return () => clearInterval(timer);
  }, [page, limit, eventType, device, verified, startDate, endDate]);

  return (
    <div className="layout">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      <main className="main">
        <Header
          backendOnline={backendOnline}
          lastUpdated={lastUpdated}
          onRefresh={loadData}
          loading={loading}
          setCurrentPage={setCurrentPage}
        />

        {errorMessage && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            {errorMessage}
          </div>
        )}

        {currentPage === "dashboard" && (
          <DashboardPage
            stats={stats}
            alerts={alerts}
            backendOnline={backendOnline}
            lastUpdated={lastUpdated}
            setCurrentPage={setCurrentPage}
          />
        )}

        {currentPage === "alerts" && (
          <AlertsPage
            alerts={alerts}
            total={total}
            totalPages={totalPages}
            page={page}
            setPage={setPage}
            limit={limit}
            setLimit={(value) => {
              setPage(1);
              setLimit(value);
            }}
            eventType={eventType}
            setEventType={setEventType}
            device={device}
            setDevice={setDevice}
            verified={verified}
            setVerified={setVerified}
            startDate={startDate}
            setStartDate={setStartDate}
            endDate={endDate}
            setEndDate={setEndDate}
            onApply={() => {
              setPage(1);
              loadData();
            }}
            onReset={resetFilters}
            onOpenAlert={setSelectedAlert}
            onVerify={handleVerify}
          />
        )}

        {currentPage === "devices" && (
          <DevicesPage stats={stats} alerts={alerts} />
        )}

        {currentPage === "drivers" && <DriversPage />}

        {currentPage === "settings" && <SettingsPage />}
      </main>

      <EvidenceModal
        alert={selectedAlert}
        verificationResult={
          selectedAlert ? verificationResults[selectedAlert.id] : null
        }
        onClose={() => setSelectedAlert(null)}
        onVerify={handleVerify}
        onManualReview={handleManualReview}
        verifying={selectedAlert ? verifyingId === selectedAlert.id : false}
      />
    </div>
  );
}
