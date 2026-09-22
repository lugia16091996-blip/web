import io
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_full_book_pdf(book_pages, book_title="Cuốn sách"):
    buffer = io.BytesIO()
    
    # Đăng ký font tiếng Việt
    font_path = os.path.join(os.path.dirname(__file__), "../assets/Merriweather_24pt-Regular.ttf")
    font_name = 'VietnameseFont' if os.path.exists(font_path) else 'Helvetica'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('VietnameseFont', font_path))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=55,
        leftMargin=55,
        topMargin=65,
        bottomMargin=55
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'BookTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        leading=28,
        alignment=1, # Center
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=15
    )
    
    # Style chuẩn cho văn bản thông thường
    body_style = ParagraphStyle(
        'BookBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,
        leading=26,
        textColor=colors.HexColor("#292524"),
        spaceAfter=10,
        leftIndent=0,
        alignment=4,         # 4 = TA_JUSTIFY (Căn đều 2 bên)
        wordWrap='CJK'       # Tránh ngắt từ lỗi đối với tiếng Việt/Unicode
    )

    # Style riêng cho các đoạn hội thoại
    dialogue_style = ParagraphStyle(
        'BookDialogue',
        parent=body_style,
        leftIndent=20,
        spaceBefore=4,
        spaceAfter=6
    )

    def draw_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#fbf7ee"))
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        
        if canvas._pageNumber > 1:
            canvas.setFont(font_name, 9)
            canvas.setFillColor(colors.HexColor("#78716c"))
            canvas.drawString(55, A4[1] - 35, f"Sách: {book_title}")
            canvas.setStrokeColor(colors.HexColor("#e7e5e4"))
            canvas.setLineWidth(0.75)
            canvas.line(55, A4[1] - 42, A4[0] - 55, A4[1] - 42)
        canvas.restoreState()

    story.append(Paragraph(f"<b>{book_title}</b>", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#d79922"), spaceAfter=20))

    # --- BƯỚC XỬ LÝ CHUỖI VĂN BẢN ĐÚNG CÁCH ---
    
    # 1. Gom toàn bộ trang lại
    full_text = "\n".join([page_text for page_text in book_pages if page_text])
    
    # 2. Xóa các dấu gạch nối ngắt từ ở cuối dòng (ví dụ: "sá-\nch" -> "sách")
    full_text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', full_text)
    
    # 3. Chuẩn hóa khoảng trắng và dấu xuống dòng rác
    # Thay thế 1 hoặc nhiều newline bằng 1 khoảng trắng duy nhất
    full_text = re.sub(r'\r\n|\r|\n', ' ', full_text)
    
    # Gộp nhiều khoảng trắng liền nhau thành 1 khoảng trắng
    full_text = re.sub(r'[ \t]+', ' ', full_text).strip()

    # 4. Tách dòng thông minh cho hội thoại & dấu hai chấm
    formatted_text = re.sub(r'\s*[-–—]\s+', '\n- ', full_text)
    
    # LƯU Ý: Việc tách dòng ở tất cả dấu hai chấm (:) có thể làm vỡ câu bình thường.
    # Nên dùng regex cẩn thận hơn chỉ tách khi là lời thoại/mục liệt kê:
    formatted_text = re.sub(r':\s*\n?', ':\n', formatted_text)

    # 5. Phân đoạn và tạo Paragraph
    paragraphs = formatted_text.split('\n')

    for para in paragraphs:
        clean_para = para.strip()
        if not clean_para:
            continue
            
        if clean_para.startswith(("-", "–", "—")):
            story.append(Paragraph(clean_para, dialogue_style))
        else:
            story.append(Paragraph(clean_para, body_style))

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()