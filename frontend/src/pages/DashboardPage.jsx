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

export function DashboardPage({
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
