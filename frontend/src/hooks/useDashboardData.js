import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchAlerts,
  fetchHealth,
  fetchRecentAlerts,
  fetchStatistics,
  manualReviewAlert,
  verifyAlert,
  deleteAlert,
} from "../api.js";
import { DEFAULT_LIMIT } from "../constants/pagination.js";

export function useDashboardData() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [eventType, setEventType] = useState("");
  const [device, setDevice] = useState("");
  const [verified, setVerified] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const [selectedAlert, setSelectedAlert] = useState(null);
  const [verificationResults, setVerificationResults] = useState({});
  const [verifyingId, setVerifyingId] = useState(null);
  const [isBatchVerifying, setIsBatchVerifying] = useState(false);
  const [isBatchDeleting, setIsBatchDeleting] = useState(false);

  const skip = useMemo(() => (page - 1) * limit, [page, limit]);

  const loadData = useCallback(
    async (overrides = {}) => {
      const nextPage = overrides.page ?? page;
      const nextLimit = overrides.limit ?? limit;
      const nextSkip = (nextPage - 1) * nextLimit;

      setLoading(true);
      setErrorMessage("");

      try {
        await fetchHealth();
        setBackendOnline(true);

        const params = {
          skip: overrides.skip ?? nextSkip,
          limit: nextLimit,
          event_type: eventType,
          device,
          verified,
          start_date: startDate,
          end_date: endDate ? `${endDate}T23:59:59` : "",
        };

        const [statsData, alertsData, recentData] = await Promise.all([
          fetchStatistics(),
          fetchAlerts(params),
          fetchRecentAlerts(24),
        ]);

        setStats(statsData);
        setAlerts(alertsData.items || []);
        setRecentAlerts(recentData.items || []);
        setTotal(alertsData.total || 0);
        setTotalPages(alertsData.total_pages || 1);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (error) {
        setBackendOnline(false);
        setErrorMessage(error.message || "Failed to fetch");
      } finally {
        setLoading(false);
      }
    },
    [device, endDate, eventType, limit, page, startDate, verified],
  );

  const handleVerify = useCallback(
    async (alertId) => {
      setVerifyingId(alertId);
      setErrorMessage("");

      try {
        const result = await verifyAlert(alertId);
        setVerificationResults((prev) => ({ ...prev, [alertId]: result }));
        await loadData();
      } catch (error) {
        setErrorMessage(error.message || "Verify failed");
      } finally {
        setVerifyingId(null);
      }
    },
    [loadData],
  );

  const handleBatchVerify = useCallback(
    async (alertIds) => {
      if (!alertIds || alertIds.length === 0) return;
      setIsBatchVerifying(true);
      setErrorMessage("");

      let successCount = 0;
      for (const id of alertIds) {
        setVerifyingId(id);
        try {
          const result = await verifyAlert(id);
          setVerificationResults((prev) => ({ ...prev, [id]: result }));
          successCount++;
        } catch (error) {
          console.error(`Verify failed for ${id}:`, error);
        }
      }

      setVerifyingId(null);
      setIsBatchVerifying(false);
      await loadData();

      if (successCount < alertIds.length) {
        setErrorMessage(
          `Batch verify completed: ${successCount}/${alertIds.length} succeeded.`,
        );
      }
    },
    [loadData],
  );

  const handleBatchDelete = useCallback(
    async (alertIds) => {
      if (!alertIds || alertIds.length === 0) return;

      const confirmDelete = window.confirm(
        `Bạn có chắc chắn muốn xoá ${alertIds.length} cảnh báo này không? Thao tác này không thể hoàn tác.`,
      );
      if (!confirmDelete) return;

      setIsBatchDeleting(true);
      setErrorMessage("");

      let successCount = 0;
      for (const id of alertIds) {
        try {
          await deleteAlert(id);
          successCount++;
        } catch (error) {
          console.error(`Delete failed for ${id}:`, error);
        }
      }

      setIsBatchDeleting(false);
      await loadData();

      if (successCount < alertIds.length) {
        setErrorMessage(
          `Xóa hoàn tất: ${successCount}/${alertIds.length} thành công.`,
        );
      }
    },
    [loadData],
  );

  const handleManualReview = useCallback(
    async (alertId, payload) => {
      setLoading(true);
      setErrorMessage("");

      try {
        await manualReviewAlert(alertId, payload);
        await loadData();
        setSelectedAlert(null);
      } catch (error) {
        setErrorMessage(error.message || "Manual review failed");
      } finally {
        setLoading(false);
      }
    },
    [loadData],
  );

  function resetFilters() {
    setEventType("");
    setDevice("");
    setVerified("");
    setStartDate("");
    setEndDate("");
    setLimit(DEFAULT_LIMIT);
    setPage(1);
  }

  useEffect(() => {
    void Promise.resolve().then(() => loadData());
    // Filters are applied explicitly from the Alerts page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, limit]);

  useEffect(() => {
    const timer = setInterval(loadData, 5000);
    return () => clearInterval(timer);
  }, [loadData]);

  return {
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
    skip,
    startDate,
    stats,
    total,
    totalPages,
    verificationResults,
    verified,
    verifyingId,
  };
}
