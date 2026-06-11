"""
Script tạo file báo cáo mới với phần tham khảo được chỉnh sửa:
- Loại bỏ các tham khảo là website (GitHub, Kaggle, trang web)
- Sắp xếp lại theo thứ tự ABC
- Format đúng theo yêu cầu nhà trường
"""
import copy
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree

INPUT_FILE = r'D:\QNU\KLTN\driver_behavior_hybrid\backend\baocao\KhoaLuan_TaiXeXeKhach_Final_v2.docx'
OUTPUT_FILE = r'D:\QNU\KLTN\driver_behavior_hybrid\backend\baocao\KhoaLuan_TaiXeXeKhach_Final_v3.docx'

# ============================================================
# Danh mục tham khảo mới (đã lọc bỏ website, sắp xếp ABC)
# ============================================================

# Tài liệu tiếng Việt (sắp xếp ABC theo tên cơ quan)
references_vi = [
    'Ủy ban An toàn Giao thông Quốc gia Việt Nam (2023), Báo cáo thường niên về tình hình tai nạn giao thông đường bộ tại Việt Nam, Hà Nội.',
    'Tổ chức Y tế Thế giới (WHO) (2023), Báo cáo tình trạng an toàn giao thông đường bộ toàn cầu, Geneva.',
]

# Tài liệu tiếng Anh (sắp xếp ABC theo họ tác giả)
references_en = [
    'Bazarevsky, V., Grishchenko, I., Raveendran, K., Zhu, F., Zhang, F., and Grundmann, M. (2020), "BlazePose: On-device Real-time Body Pose tracking," arXiv preprint arXiv:2006.10204.',
    'Bradski, G. (2000), "The OpenCV Library," Dr. Dobb\'s Journal of Software Tools, 25(11), pp. 120-125.',
    'Carion, N., Massa, F., Synnaeve, G., Usunier, N., Kirillov, A., and Zagoruyko, S. (2020), "End-to-End Object Detection with Transformers," In Proceedings of the European Conference on Computer Vision (ECCV), pp. 213-229.',
    'Fan, H., Xiong, B., Mangalam, K., Li, Y., Yan, Z., Malik, J., and Feichtenhofer, C. (2021), "Multiscale Vision Transformers," In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), pp. 6824-6835.',
    'Feichtenhofer, C., Fan, H., Malik, J., and He, K. (2019), "SlowFast Networks for Video Recognition," In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), pp. 6202-6211.',
    'He, K., Zhang, X., Ren, S., and Sun, J. (2016), "Deep Residual Learning for Image Recognition," In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 770-778.',
    'Jacob, B., Kligys, S., Chen, B., Zhu, M., Tang, M., Howard, A., Adam, H., and Kalenichenko, D. (2018), "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference," In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 2704-2713.',
    'Kingma, D.P. and Ba, J. (2015), "Adam: A Method for Stochastic Optimization," In Proceedings of the International Conference on Learning Representations (ICLR).',
    'Lin, T.Y., Dollár, P., Girshick, R., He, K., Hariharan, B., and Belongie, S. (2017), "Feature Pyramid Networks for Object Detection," In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 2117-2125.',
    'Liu, W., Anguelov, D., Erhan, D., Szegedy, C., Reed, S., Fu, C.Y., and Berg, A.C. (2016), "SSD: Single Shot MultiBox Detector," In Proceedings of the European Conference on Computer Vision (ECCV), pp. 21-37.',
    'Lugaresi, C., Tang, J., Nash, H., McClanahan, C., Uboweja, E., Hays, M., Zhang, F., Chang, C., Yong, M.G., Lee, J., Chang, W., Hua, W., Georg, M., and Grundmann, M. (2019), "MediaPipe: A Framework for Building Perception Pipelines," arXiv preprint arXiv:1906.08172.',
    'Ramstedt, S. and Pal, C. (2017), "Real-time Traffic Sign Detection, Classification and Post-Processing," arXiv preprint arXiv:1709.07897.',
    'Redmon, J. and Farhadi, A. (2018), "YOLOv3: An Incremental Improvement," arXiv preprint arXiv:1804.02767.',
    'Redmon, J., Divvala, S., Girshick, R., and Farhadi, A. (2016), "You Only Look Once: Unified, Real-Time Object Detection," In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 779-788.',
    'Ren, S., He, K., Girshick, R., and Sun, J. (2015), "Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks," In Proceedings of the Advances in Neural Information Processing Systems (NeurIPS), pp. 91-99.',
]


def create_paragraph_element(text, font_name='Times New Roman', font_size=12, bold=False, italic=False, alignment=None):
    """Tạo một paragraph element XML với định dạng specified."""
    # Tạo paragraph element
    p = OxmlElement('w:p')

    # Paragraph properties
    pPr = OxmlElement('w:pPr')
    if alignment:
        jc = OxmlElement('w:jc')
        jc.set(qn('w:val'), alignment)
        pPr.append(jc)
    # Line spacing 1.5
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:line'), '360')
    spacing.set(qn('w:lineRule'), 'auto')
    pPr.append(spacing)
    # Paragraph indent (hanging 1.25cm ~ 720 twips for references)
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), '720')
    ind.set(qn('w:hanging'), '720')
    pPr.append(ind)
    p.append(pPr)

    # Run
    run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(int(font_size * 2)))  # half-points
    rPr.append(sz)
    szCs = OxmlElement('w:szCs')
    szCs.set(qn('w:val'), str(int(font_size * 2)))
    rPr.append(szCs)
    if bold:
        b = OxmlElement('w:b')
        rPr.append(b)
    if italic:
        i = OxmlElement('w:i')
        rPr.append(i)
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '000000')
    rPr.append(color)
    run.append(rPr)
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    run.append(t)
    p.append(run)

    return p


def main():
    doc = Document(INPUT_FILE)
    body = doc.element.body
    para_elements = list(body.findall(qn('w:p')))

    # --- Bước 1: Xác định vị trí cần xóa ---
    # Tiêu đề "TÀI LIỆU THAM KHẢO" ở paragraph index 2676
    # Nội dung tham khảo cũ: paragraphs 2677 -> 2784 (trước "PHỤ LỤC" ở 2785)
    ref_title_idx = 2676
    ref_end_idx = 2785  # PHỤ LỤC - không xóa

    # Xác định paragraph element của tiêu đề
    ref_title_elem = para_elements[ref_title_idx]

    # --- Bước 2: Xóa tất cả nội dung cũ sau tiêu đề (2677 -> 2784) ---
    # Thu thập tất cả elements cần xóa (paragraphs + any elements between)
    elements_to_remove = []
    for i in range(ref_title_idx + 1, ref_end_idx):
        elements_to_remove.append(para_elements[i])

    # Xóa các elements
    for elem in elements_to_remove:
        body.remove(elem)

    # --- Bước 3: Chèn nội dung mới sau tiêu đề ---
    # Tìm vị trí chèn: ngay sau ref_title_elem
    insert_after = ref_title_elem

    # Danh mục tham khảo tiếng Việt
    vi_header = create_paragraph_element('Tài liệu tiếng Việt:', font_size=12, bold=False)
    insert_after.addnext(vi_header)
    insert_after = vi_header

    for i, ref_text in enumerate(references_vi, 1):
        ref_str = f'[{i}] {ref_text}'
        ref_para = create_paragraph_element(ref_str, font_size=12)
        insert_after.addnext(ref_para)
        insert_after = ref_para

    # Danh mục tham khảo tiếng nước ngoài
    blank_line = create_paragraph_element('', font_size=12)
    insert_after.addnext(blank_line)
    insert_after = blank_line

    en_header = create_paragraph_element('Tài liệu tiếng nước ngoài:', font_size=12, bold=False)
    insert_after.addnext(en_header)
    insert_after = en_header

    for i, ref_text in enumerate(references_en, len(references_vi) + 1):
        ref_str = f'[{i}] {ref_text}'
        ref_para = create_paragraph_element(ref_str, font_size=12)
        insert_after.addnext(ref_para)
        insert_after = ref_para

    # Thêm dòng trống trước PHỤ LỤC
    blank = create_paragraph_element('', font_size=12)
    insert_after.addnext(blank)

    # --- Bước 4: Lưu file mới ---
    doc.save(OUTPUT_FILE)
    print(f'Da tao file thanh cong: {OUTPUT_FILE}')
    print(f'Tong so tai lieu tham khao: {len(references_vi) + len(references_en)}')
    print(f'  - Tieng Viet: {len(references_vi)}')
    print(f'  - Tieng nuoc ngoai: {len(references_en)}')


if __name__ == '__main__':
    main()
