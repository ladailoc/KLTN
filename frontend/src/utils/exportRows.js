export function exportRows(rows) {
  if (!rows.length) {
    alert("Không có dữ liệu để export");
    return;
  }

  const columns = [
    { key: "id", label: "ALERT ID" },
    { key: "timestamp", label: "TIMESTAMP" },
    { key: "event_type", label: "EVENT TYPE" },
    { key: "confidence", label: "CONFIDENCE" },
    { key: "frame_index", label: "FRAME INDEX" },
    { key: "source_device", label: "SOURCE DEVICE" },
    { key: "verified", label: "VERIFIED" },
    { key: "review_status", label: "REVIEW STATUS" },
    { key: "notes", label: "NOTES" },
  ];

  const headerRow = columns.map((col) => `"${col.label}"`).join(",");

  const csvRows = [
    headerRow,
    ...rows.map((row) =>
      columns
        .map((col) => `"${String(row[col.key] ?? "").replaceAll('"', '""')}"`)
        .join(","),
    ),
  ];

  // Thêm BOM (\uFEFF) và cờ "sep=," để Excel Việt Nam tự động hiểu dấu phẩy là cột phân cách
  const csvContent = "sep=,\r\n" + csvRows.join("\r\n");

  const blob = new Blob(["\uFEFF" + csvContent], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "alerts_export.csv";
  a.click();

  URL.revokeObjectURL(url);
}
