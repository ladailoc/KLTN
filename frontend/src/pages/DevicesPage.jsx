import { MonitorDot } from "lucide-react";

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
