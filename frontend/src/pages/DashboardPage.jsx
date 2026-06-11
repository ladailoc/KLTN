import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ChevronRight,
  Cigarette,
  HardDrive,
  MonitorDot,
  Shield,
  ShieldCheck,
  Smartphone,
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

import { StatCard } from "../components/common/StatCard.jsx";
import {
  buildDeviceData,
  buildPieData,
  buildTrendData,
  getEventCount,
  getTopDevice,
} from "../utils/dashboardData.js";
import { formatNumber } from "../utils/formatters.js";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--navy)",
      color: "#fff",
      padding: "8px 14px",
      borderRadius: "var(--radius-sm)",
      fontSize: "12px",
      fontWeight: 600,
      boxShadow: "var(--shadow-md)",
      border: "none",
    }}>
      <div style={{ opacity: 0.7, marginBottom: "2px", fontSize: "11px" }}>{label}</div>
      <div>{payload[0].value} alerts</div>
    </div>
  );
};

export function DashboardPage({
  stats,
  alerts,
  recentAlerts,
  backendOnline,
  lastUpdated,
  setCurrentPage,
}) {
  const total = stats?.total_alerts || 0;
  const verified = stats?.verified_count || 0;
  const verifiedRate =
    total > 0 ? ((verified / total) * 100).toFixed(1) : "0.0";

  const last24h = stats?.last_24h_count || 0;
  const prev24h = stats?.prev_24h_count || 0;
  let changeBadge = "No data";
  if (prev24h > 0) {
    const pct = (((last24h - prev24h) / prev24h) * 100).toFixed(0);
    changeBadge = `${last24h - prev24h >= 0 ? "+" : ""}${pct}% vs prev 24h`;
  } else if (last24h > 0) {
    changeBadge = `${last24h} new in 24h`;
  }

  const rateNum = parseFloat(verifiedRate);
  const rateBadge =
    total === 0
      ? "No alerts"
      : rateNum >= 80
        ? "High"
        : rateNum >= 50
          ? "Moderate"
          : "Low";

  const phoneCount = getEventCount(stats, "using_phone");
  const smokingCount = getEventCount(stats, "smoking");
  const seatbeltCount = getEventCount(stats, "no_seatbelt");

  const pieData = buildPieData(stats);
  const deviceData = buildDeviceData(stats);
  const trendData = buildTrendData(recentAlerts);

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
          badge={changeBadge}
          colorClass="danger"
        />
        <StatCard
          label="Verified Rate"
          value={`${verifiedRate}%`}
          icon={ShieldCheck}
          badge={rateBadge}
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
            <BarChart data={trendData} barSize={32}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#edf0f5" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 11, fill: "#6b7a90" }}
                axisLine={{ stroke: "#edf0f5" }}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: "#6b7a90" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(91, 91, 214, 0.04)" }} />
              <Bar dataKey="alerts" fill="#c7d2fe" radius={[6, 6, 0, 0]} />
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
                    stroke="none"
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>

              <div className="donut-mini-center">
                <strong>{formatNumber(total)}</strong>
                <span>Total Events</span>
              </div>
            </div>

            <div className="event-list">
              {pieData.length === 0 ? (
                <p style={{ color: "var(--muted)", fontSize: "13px" }}>No event data</p>
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
              <BarChart data={deviceData} barSize={40}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#edf0f5" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#6b7a90" }}
                  axisLine={{ stroke: "#edf0f5" }}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11, fill: "#6b7a90" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(91, 91, 214, 0.04)" }} />
                <Bar dataKey="alerts" fill="#1a2744" radius={[6, 6, 0, 0]} />
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
