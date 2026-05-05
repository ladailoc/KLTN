export function SettingsPage() {
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
