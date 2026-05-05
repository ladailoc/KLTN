import { MonitorDot, Plus, Wifi } from "lucide-react";

export function DevicesPage({ stats, alerts }) {
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
        <button className="primary-btn">
          <Plus size={16} /> Add Device
        </button>
      </section>

      <section className="device-grid">
        {devices.length === 0 ? (
          <div className="empty-box" style={{ gridColumn: "1 / -1" }}>
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "12px",
            }}>
              <Wifi size={40} style={{ color: "var(--line)", strokeWidth: 1.5 }} />
              <div style={{ textAlign: "center" }}>
                <div style={{ fontWeight: 700, fontSize: "14px", marginBottom: "4px" }}>
                  No devices connected
                </div>
                <div style={{ fontSize: "12px" }}>
                  Edge devices will appear here once they start reporting.
                </div>
              </div>
            </div>
          </div>
        ) : (
          devices.map((device) => (
            <div className="device-card" key={device.id}>
              <div className="device-card-top">
                <div className="device-icon">
                  <MonitorDot size={22} />
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
