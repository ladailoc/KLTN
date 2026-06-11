"""
Script sửa diễn giải FPS trong bản báo cáo chính thức:
- Sửa đoạn [533]: diễn giải kết quả FPS sau Bảng 4.1
- Giải thích rõ ý nghĩa của FPS khi sử dụng frame skipping
Chạy: python -X utf8 fix_fps_interpretation.py
"""
from docx import Document

doc = Document(r"4551050116_La Dai Loc_Bao cao KLTN.docx")


def replace_paragraph_text(para, old_text, new_text):
    full_text = para.text
    if old_text not in full_text:
        return False
    new_full = full_text.replace(old_text, new_text)
    if para.runs:
        first_run = para.runs[0]
        font_name = first_run.font.name
        font_size = first_run.font.size
        font_bold = first_run.font.bold
        font_italic = first_run.font.italic
    else:
        font_name = font_size = font_bold = font_italic = None
    for run in para.runs:
        run.text = ""
    if para.runs:
        para.runs[0].text = new_full
        if font_name:
            para.runs[0].font.name = font_name
        if font_size:
            para.runs[0].font.size = font_size
        if font_bold is not None:
            para.runs[0].font.bold = font_bold
        if font_italic is not None:
            para.runs[0].font.italic = font_italic
    return True


edits_done = 0

# ============================================================================
# SỬA 1: Đoạn [533] - Diễn giải kết quả FPS sau Bảng 4.1
# ============================================================================
print("=== [1] Fix FPS interpretation (Paragraph 533) ===")

old_text = (
    "Qua phân tích số liệu, có thể thấy rõ quy luật đánh đổi tài nguyên. "
    "Khi kích hoạt thêm mô hình ước lượng tư thế MediaPipe, tải điện toán "
    "(computational load) tăng vọt khiến FPS suy giảm đáng kể so với cấu hình "
    "chỉ chạy YOLO. Tuy nhiên, nhờ cơ chế kích hoạt pose theo điều kiện kết hợp "
    "bỏ khung hình và thu nhỏ không gian ảnh, pipeline có thể duy trì mức FPS "
    "đáp ứng tiêu chí thời gian thực trong điều kiện cấu hình phù hợp."
)

new_text = (
    "Qua phân tích số liệu, có thể thấy rõ quy luật đánh đổi tài nguyên. "
    "Khi kích hoạt thêm mô hình ước lượng tư thế MediaPipe, tải điện toán "
    "(computational load) tăng vọt khiến FPS suy giảm đáng kể so với cấu hình "
    "chỉ chạy YOLO. Ở các cấu hình có frame skipping (N=3), chỉ số FPS đo được "
    "phản ánh thông lượng suy luận thực tế của pipeline trong điều kiện lấy mẫu "
    "thưa, không phải tốc độ hiển thị hình ảnh đầu ra. Cụ thể, mô hình YOLO chỉ "
    "được gọi suy luận mỗi 3 frame một lần, còn các frame trung gian sử dụng kết "
    "quả phát hiện từ frame trước, giúp giảm tải tài nguyên tính toán. Kỹ thuật "
    "resize ảnh đầu vào (từ 848 xuống 640 pixel) giúp rút ngắn thời gian suy luận "
    "trên mỗi frame, cải thiện thông lượng từ 3.13 lên 3.85 FPS. Hệ thống được "
    "thiết kế hướng tới triển khai trên thiết bị Edge chuyên dụng, nơi các tối ưu "
    "phần cứng (NPU, GPU nhúng) có thể tiếp tục nâng cao hiệu năng đáp ứng tiêu "
    "chí thời gian thực."
)

found = False
for i, para in enumerate(doc.paragraphs):
    if "Qua phân tích số liệu" in para.text:
        if replace_paragraph_text(para, old_text, new_text):
            print(f"  [OK] Replaced at paragraph {i}")
            found = True
            edits_done += 1
            break
        else:
            # Try shorter match
            shorter_old = "Qua phân tích số liệu, có thể thấy rõ quy luật đánh đổi tài nguyên"
            shorter_new = (
                "Qua phân tích số liệu, có thể thấy rõ quy luật đánh đổi tài nguyên. "
                "Khi kích hoạt thêm mô hình ước lượng tư thế MediaPipe, tải điện toán "
                "(computational load) tăng vọt khiến FPS suy giảm đáng kể so với cấu hình "
                "chỉ chạy YOLO. Ở các cấu hình có frame skipping (N=3), chỉ số FPS đo được "
                "phản ánh thông lượng suy luận thực tế của pipeline trong điều kiện lấy mẫu "
                "thưa, không phải tốc độ hiển thị hình ảnh đầu ra. Cụ thể, mô hình YOLO chỉ "
                "được gọi suy luận mỗi 3 frame một lần, còn các frame trung gian sử dụng kết "
                "quả phát hiện từ frame trước, giúp giảm tải tài nguyên tính toán. Kỹ thuật "
                "resize ảnh đầu vào (từ 848 xuống 640 pixel) giúp rút ngắn thời gian suy luận "
                "trên mỗi frame, cải thiện thông lượng từ 3.13 lên 3.85 FPS. Hệ thống được "
                "thiết kế hướng tới triển khai trên thiết bị Edge chuyên dụng, nơi các tối ưu "
                "phần cứng (NPU, GPU nhúng) có thể tiếp tục nâng cao hiệu năng đáp ứng tiêu "
                "chí thời gian thực."
            )
            if replace_paragraph_text(para, shorter_old, shorter_new):
                print(f"  [OK] Replaced (shorter match) at paragraph {i}")
                found = True
                edits_done += 1
                break

if not found:
    print("  [SKIP] Text not found")

# ============================================================================
# LƯU FILE
# ============================================================================
output_path = r"4551050116_La Dai Loc_Bao cao KLTN.docx"
doc.save(output_path)
print(f"\n{'='*60}")
print(f"Tổng kết: {edits_done} sửa/thêm thành công")
print(f"File đã chỉnh sửa: {output_path}")
print(f"{'='*60}")
