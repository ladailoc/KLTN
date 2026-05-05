import {
  AlertTriangle,
  CalendarClock,
  ChevronRight,
  Download,
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
            <BarChart data={FLEET_SCORE_DATA}>
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
