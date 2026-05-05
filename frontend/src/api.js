const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export function getMediaUrl(path) {
  if (!path) return null;

  if (path.startsWith("http")) {
    return path;
  }

  if (path.startsWith("/")) {
    return `${API_BASE_URL}${path}`;
  }

  return `${API_BASE_URL}/${path}`;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error("Backend API is offline");
  }
  return response.json();
}

export async function fetchStatistics() {
  const response = await fetch(`${API_BASE_URL}/api/statistics`);
  if (!response.ok) {
    throw new Error("Không tải được dữ liệu thống kê");
  }
  return response.json();
}

export async function fetchAlerts(params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });

  const response = await fetch(
    `${API_BASE_URL}/api/alerts?${query.toString()}`,
  );
  if (!response.ok) {
    throw new Error("Không tải được danh sách cảnh báo");
  }

  return response.json();
}

export async function manualReviewAlert(alertId, payload) {
  const response = await fetch(
    `${API_BASE_URL}/alerts/${alertId}/manual_review`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Không lưu được đánh giá thủ công");
  }

  return response.json();
}

export async function verifyAlert(alertId) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/verify`, {
    method: "POST",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail || "Không xác thực được cảnh báo bằng SlowFast",
    );
  }

  return response.json();
}

export async function deleteAlert(alertId) {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Không thể xoá cảnh báo");
  }

  return response.json();
}
