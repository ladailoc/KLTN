import { useState } from "react";
import { Loader2, ShieldCheck, Video, X, Zap, FileJson } from "lucide-react";

import { getMediaUrl } from "../../api.js";
import { getEventMeta } from "../../constants/events.jsx";
import { formatConfidence } from "../../utils/formatters.js";

export function EvidenceModal({
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
    <div className="modal-backdrop" onClick={onClose}>
      <div className="alert-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-top">
          <div>
            <h2>Alert Details — #EV-{String(alert.id).padStart(3, "0")}</h2>
            <div className="modal-subline">
              <span className={`modal-event-pill ${meta.className}`}>
                {meta.label}
              </span>
              <span>Timestamp: {alert.timestamp || "-"}</span>
            </div>
          </div>

          <button className="close-btn" onClick={onClose}>
            <X size={20} />
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
                  <Video size={36} />
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
                <FileJson size={14} /> View JSON Event
              </a>
            )}

            <button
              className="slowfast-btn"
              onClick={() => onVerify(alert.id)}
              disabled={!clipUrl || verifying}
            >
              {verifying ? (
                <Loader2 className="spin" size={20} />
              ) : (
                <Zap size={20} />
              )}
              {verifying ? "Verifying..." : "Verify with SlowFast AI"}
            </button>
          </div>

          <div className="metadata-column">
            <div className="metadata-card">
              <h3>Technical Metadata</h3>
              <div className="meta-row">
                <span>Alert ID</span>
                <strong style={{ fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: "12.5px" }}>
                  #EV-{String(alert.id).padStart(3, "0")}
                </strong>
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
                <strong style={{ textTransform: "capitalize" }}>
                  {alert.review_status ||
                    (alert.verified ? "verified" : "pending")}
                </strong>
              </div>
            </div>

            <div className="reviewer-card">
              <h3>Reviewer Notes</h3>
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
            <ShieldCheck size={20} />
            <h3>SlowFast Verification Result</h3>
          </div>

          {verificationResult ? (
            <div className="verify-grid">
              <div>
                <span>Status</span>
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
                <span>Predicted Event</span>
                <strong>
                  {verificationResult.predicted_project_event || "-"}
                </strong>
              </div>

              <div>
                <span>Predicted Score</span>
                <strong>
                  {verificationResult.predicted_project_score ?? "-"}
                </strong>
              </div>

              <div>
                <span>Top-K Labels</span>
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
              No verification results yet. Run SlowFast or verify manually.
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
