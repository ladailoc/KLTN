import sys
import io
from docx import Document

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

doc = Document('báo cáo_final.docx')

# Citation rules: (pattern_to_find, citation_number, context_hint)
# Order: more specific patterns first to avoid duplicate matches
citation_rules = [
    # [14] Redmon et al. (2016) - Original YOLO
    ("YOLO (You Only Look Once)", 14),
    ("YOLO phân hoạch ảnh đầu vào", 14),

    # [13] Redmon & Farhadi (2018) - YOLOv3 (if mentioned)
    ("YOLOv3", 13),

    # [15] Ren et al. (2015) - Faster R-CNN
    ("Faster R-CNN", 15),

    # [10] Liu et al. (2016) - SSD
    ("SSD: Single Shot MultiBox Detector", 10),
    ("SSD", 10),

    # [5] Feichtenhofer et al. (2019) - SlowFast
    ("SlowFast Networks", 5),
    ("SlowFast là một kiến trúc mạng nơ-ron", 5),

    # [11] Lugaresi et al. (2019) - MediaPipe
    ("MediaPipe Pose cung cấp khả năng phát hiện tối đa 33 điểm mốc", 11),
    ("MediaPipe là một bộ khung", 11),

    # [1] Bazarevsky et al. (2020) - BlazePose
    ("BlazePose", 1),

    # [2] Bradski (2000) - OpenCV
    ("OpenCV VideoCapture", 2),
    ("OpenCV", 2),

    # [7] Jacob et al. (2018) - Quantization
    ("Quantization", 7),

    # [6] He et al. (2016) - ResNet (mention residual connections in YOLO backbone)
    ("khối tích chập kết hợp cơ chế tàn dư", 6),
    ("Residual connections", 6),

    # [9] Lin et al. (2017) - Feature Pyramid Networks
    ("hợp nhất các bản đồ đặc trưng", 9),
    ("bảo toàn đặc trưng đa tỉ lệ", 9),

    # [8] Kingma & Ba (2015) - Adam (if mentioned in training section)
    ("Adam", 8),

    # [3] Carion et al. (2020) - DETR
    ("RT-DETR", 3),
    ("DETR", 3),

    # [4] Fan et al. (2021) - MViT
    ("MViT", 4),
    ("Multiscale Vision Transformers", 4),

    # [12] Ramstedt & Pal (2017) - Traffic sign detection
    ("phát hiện biển báo", 12),
]


def add_citation_to_paragraph(para, pattern, cite_num):
    """Add citation [N] after the first occurrence of pattern in paragraph runs."""
    text = para.text
    cite_marker = f'[{cite_num}]'

    # Skip if citation already exists
    if cite_marker in text:
        return False

    # Find pattern
    idx = text.find(pattern)
    if idx == -1:
        idx = text.lower().find(pattern.lower())
        if idx == -1:
            return False

    insert_pos = idx + len(pattern)

    # Don't insert if next char is already a bracket
    if insert_pos < len(text) and text[insert_pos] == '[':
        return False

    # Find which run contains the insertion point
    char_count = 0
    for run in para.runs:
        run_len = len(run.text)
        if char_count + run_len >= insert_pos:
            offset = insert_pos - char_count
            run.text = run.text[:offset] + cite_marker + run.text[offset:]
            return True
        char_count += run_len

    return False


# Keywords to skip
skip_keywords = ['TÀI LIỆU THAM KHẢO', 'LỜI CẢM ƠN', 'DANH MỤC', 'TÓM TẮT']

changes_log = []

for para_idx, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if not text:
        continue

    # Stop at references section
    if text.startswith('TÀI LIỆU THAM KHẢO'):
        break

    # Skip reference items
    if text.startswith('[1]') or text.startswith('[2]') or text.startswith('[3]'):
        continue

    # Skip certain sections
    if any(kw in text for kw in skip_keywords):
        continue

    # Skip very short paragraphs
    if len(text) < 20:
        continue

    # Try each citation rule
    added_in_para = set()
    for pattern, cite_num in citation_rules:
        if cite_num in added_in_para:
            continue
        if add_citation_to_paragraph(para, pattern, cite_num):
            added_in_para.add(cite_num)
            changes_log.append(f"Para {para_idx}: Added [{cite_num}] after '{pattern[:60]}'")

# Save
output_path = 'báo cáo_final_citations.docx'
doc.save(output_path)

print(f"Total citations added: {len(changes_log)}")
print()
for log in changes_log:
    print(log)
print()
print(f"Saved to: {output_path}")
