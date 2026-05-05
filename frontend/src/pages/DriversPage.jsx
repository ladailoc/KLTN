import {
  AlertTriangle,
  CalendarClock,
  ChevronRight,
  Download,
  Plus,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { DRIVERS, FLEET_SCORE_DATA } from "../constants/drivers.js";

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
      <div>Score: {payload[0].value}</div>
    </div>
  );
};

export function DriversPage() {
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
            <Download size={15} /> Export Data
          </button>
          <button className="primary-btn">
            <Plus size={16} /> Add New Driver
          </button>
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
            <span style={{ color: "var(--muted)" }}>-</span>
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
              {DRIVERS.map((driver) => (
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
                        <span>Active · {driver.fleet}</span>
                      </div>
                    </div>
                  </td>
                  <td style={{ fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: "12.5px", fontWeight: 600 }}>
                    {driver.id}
                  </td>
                  <td style={{ fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: "12.5px" }}>
                    {driver.license}
                  </td>
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
                    <button
                      className="header-icon-btn"
                      style={{ width: "32px", height: "32px" }}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="dashboard-grid lower" style={{ marginTop: "20px" }}>
        <div className="panel">
          <div className="panel-title">
            <h2>Fleet Safety Overview</h2>
            <span>Weekly</span>
          </div>

          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={FLEET_SCORE_DATA} barSize={32}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#edf0f5" />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 11, fill: "#6b7a90" }}
                axisLine={{ stroke: "#edf0f5" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7a90" }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(91, 91, 214, 0.04)" }} />
              <Bar dataKey="score" fill="#1a2744" radius={[6, 6, 0, 0]} />
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
