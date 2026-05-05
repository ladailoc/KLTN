import { Download, Eye, CheckSquare, Trash2 } from "lucide-react";
import { useState } from "react";

import { ConfidenceBar } from "../components/alerts/ConfidenceBar.jsx";
import { EventBadge } from "../components/alerts/EventBadge.jsx";
import { StatusBadge } from "../components/alerts/StatusBadge.jsx";
import { CustomSelect } from "../components/common/CustomSelect.jsx";
import { CustomDatePicker } from "../components/common/CustomDatePicker.jsx";
import { exportRows } from "../utils/exportRows.js";
import { formatNumber } from "../utils/formatters.js";

export function AlertsPage({
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
  onBatchVerify,
  onBatchDelete,
  isBatchVerifying,
  isBatchDeleting,
}) {
  const [selectedAlerts, setSelectedAlerts] = useState(new Set());

  const toggleAlert = (alertId) => {
    const newSet = new Set(selectedAlerts);
    if (newSet.has(alertId)) {
      newSet.delete(alertId);
    } else {
      newSet.add(alertId);
    }
    setSelectedAlerts(newSet);
  };

  const toggleAll = () => {
    if (selectedAlerts.size === alerts.length && alerts.length > 0) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(alerts.map((a) => a.id)));
    }
  };

  const handleBatchVerifyClick = async () => {
    if (selectedAlerts.size === 0) return;
    const alertIds = Array.from(selectedAlerts).filter((id) => {
      const alert = alerts.find((a) => a.id === id);
      return alert && alert.clip_url && alert.verified === false;
    });

    if (alertIds.length === 0) {
      alert(
        "Không có cảnh báo nào hợp lệ để xác minh trong nhóm đã chọn (cần có video clip và ở trạng thái Pending).",
      );
      return;
    }

    await onBatchVerify(alertIds);
    setSelectedAlerts(new Set());
  };

  const handleBatchDeleteClick = async () => {
    if (selectedAlerts.size === 0) return;
    const alertIds = Array.from(selectedAlerts);
    await onBatchDelete(alertIds);
    setSelectedAlerts(new Set());
  };

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

        <div className="page-actions" style={{ display: "flex", gap: "12px" }}>
          <button className="secondary-btn" onClick={() => exportRows(alerts)}>
            <Download size={16} />
            Export CSV
          </button>

          <button
            className="secondary-btn"
            onClick={handleBatchDeleteClick}
            disabled={
              selectedAlerts.size === 0 || isBatchVerifying || isBatchDeleting
            }
            style={{
              color: selectedAlerts.size > 0 ? "var(--error)" : "inherit",
              borderColor:
                selectedAlerts.size > 0
                  ? "rgba(239, 68, 68, 0.3)"
                  : "var(--line)",
            }}
          >
            <Trash2 size={16} />
            {isBatchDeleting
              ? "Deleting..."
              : `Delete (${selectedAlerts.size})`}
          </button>

          <button
            className="primary-btn"
            onClick={handleBatchVerifyClick}
            disabled={
              selectedAlerts.size === 0 || isBatchVerifying || isBatchDeleting
            }
          >
            <CheckSquare size={16} />
            {isBatchVerifying
              ? "Verifying..."
              : `Batch Verify (${selectedAlerts.size})`}
          </button>
        </div>
      </section>

      <section className="filter-panel">
        <label>
          <span>EVENT TYPE</span>
          <CustomSelect
            value={eventType}
            onChange={(val) => setEventType(val)}
            options={[
              { value: "", label: "All Types" },
              { value: "using_phone", label: "Using Phone" },
              { value: "smoking", label: "Smoking" },
              { value: "no_seatbelt", label: "No Seatbelt" },
            ]}
          />
        </label>

        <label>
          <span>DEVICE ID</span>
          <input
            style={{ padding: "0 14px", fontSize: "14px" }}
            value={device}
            onChange={(e) => setDevice(e.target.value)}
            placeholder="All Devices"
          />
        </label>

        <label>
          <span>STATUS</span>
          <CustomSelect
            value={verified}
            onChange={(val) => setVerified(val)}
            options={[
              { value: "", label: "All Status" },
              { value: "true", label: "Verified" },
              { value: "false", label: "Pending" },
            ]}
          />
        </label>

        <label>
          <span>START DATE</span>
          <CustomDatePicker
            value={startDate}
            onChange={(val) => setStartDate(val)}
            placeholder="DD/MM/YYYY"
          />
        </label>

        <label>
          <span>END DATE</span>
          <CustomDatePicker
            value={endDate}
            onChange={(val) => setEndDate(val)}
            placeholder="DD/MM/YYYY"
          />
        </label>

        <label>
          <span>ROWS</span>
          <CustomSelect
            value={limit}
            onChange={(val) => setLimit(Number(val))}
            options={[
              { value: 10, label: "10" },
              { value: 20, label: "20" },
              { value: 50, label: "50" },
              { value: 100, label: "100" },
            ]}
          />
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
                <th style={{ width: 40, textAlign: "center" }}>
                  <input
                    type="checkbox"
                    disabled={
                      alerts.length === 0 || isBatchVerifying || isBatchDeleting
                    }
                    checked={
                      selectedAlerts.size === alerts.length && alerts.length > 0
                    }
                    onChange={toggleAll}
                  />
                </th>
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
                  <td colSpan="8" className="empty-row">
                    No alerts found
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className={
                      selectedAlerts.has(alert.id) ? "selected-row" : ""
                    }
                  >
                    <td style={{ textAlign: "center" }}>
                      <input
                        type="checkbox"
                        disabled={isBatchVerifying || isBatchDeleting}
                        checked={selectedAlerts.has(alert.id)}
                        onChange={() => toggleAlert(alert.id)}
                      />
                    </td>
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
                        <button
                          onClick={() => onOpenAlert(alert)}
                          disabled={isBatchVerifying || isBatchDeleting}
                        >
                          <Eye size={15} /> View
                        </button>
                        <button
                          className="verify-small"
                          onClick={() => onVerify(alert.id)}
                          disabled={
                            !alert.clip_url ||
                            isBatchVerifying ||
                            isBatchDeleting
                          }
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
