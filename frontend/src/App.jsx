import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";

import { EvidenceModal } from "./components/alerts/EvidenceModal.jsx";
import { Header } from "./components/layout/Header.jsx";
import { Sidebar } from "./components/layout/Sidebar.jsx";
import { useDashboardData } from "./hooks/useDashboardData.js";
import { AlertsPage } from "./pages/AlertsPage.jsx";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { DriversPage } from "./pages/DriversPage.jsx";
import { SettingsPage } from "./pages/SettingsPage.jsx";

export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [errorDismissed, setErrorDismissed] = useState(false);
  const {
    alerts,
    backendOnline,
    device,
    endDate,
    errorMessage,
    eventType,
    handleBatchVerify,
    handleBatchDelete,
    handleManualReview,
    handleVerify,
    isBatchVerifying,
    isBatchDeleting,
    lastUpdated,
    limit,
    loadData,
    loading,
    page,
    recentAlerts,
    resetFilters,
    selectedAlert,
    setDevice,
    setEndDate,
    setEventType,
    setLimit,
    setPage,
    setSelectedAlert,
    setStartDate,
    setVerified,
    startDate,
    stats,
    total,
    totalPages,
    verificationResults,
    verified,
    verifyingId,
  } = useDashboardData();

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

        {errorMessage && !errorDismissed && (
          <div className="error-banner">
            <AlertTriangle size={16} />
            <span style={{ flex: 1 }}>{errorMessage}</span>
            <button
              onClick={() => setErrorDismissed(true)}
              style={{
                background: "none",
                border: "none",
                color: "inherit",
                cursor: "pointer",
                padding: "2px",
                display: "grid",
                placeItems: "center",
                opacity: 0.6,
              }}
            >
              <X size={14} />
            </button>
          </div>
        )}

        {currentPage === "dashboard" && (
          <DashboardPage
            stats={stats}
            alerts={alerts}
            recentAlerts={recentAlerts}
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
              loadData({ page: 1 });
            }}
            onReset={resetFilters}
            onOpenAlert={setSelectedAlert}
            onVerify={handleVerify}
            onBatchVerify={handleBatchVerify}
            onBatchDelete={handleBatchDelete}
            isBatchVerifying={isBatchVerifying}
            isBatchDeleting={isBatchDeleting}
          />
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
