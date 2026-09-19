import io
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
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
        alignment=1,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=15
    )
    
    # Style chuẩn cho văn bản thông thường
    body_style = ParagraphStyle(
        'BookBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,      # Chữ lớn đọc êm mắt
        leading=26,       # Giãn dòng rộng rãi
        textColor=colors.HexColor("#292524"),
        spaceAfter=10,    # Khoảng cách vừa phải giữa các đoạn
        leftIndent=0
    )

    # Style riêng cho các đoạn hội thoại / hỏi đáp bắt đầu bằng dấu gạch ngang (-)
    dialogue_style = ParagraphStyle(
        'BookDialogue',
        parent=body_style,
        leftIndent=15,    # Thụt lề nhẹ phía bên trái giúp đoạn hội thoại trông cực kỳ chuyên nghiệp như sách in
        spaceBefore=4,
        spaceAfter=6
    )

    def draw_background(canvas, doc):
        canvas.saveState()
        # Vẽ màu nền vàng ấm toàn trang cho mọi trang PDF
        canvas.setFillColor(colors.HexColor("#fbf7ee"))
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        
        # Vẽ Running Header từ trang thứ 2 trở đi
        if canvas._pageNumber > 1:
            canvas.setFont(font_name, 9)
            canvas.setFillColor(colors.HexColor("#78716c"))
            canvas.drawString(55, A4[1] - 35, f"Sách: {book_title}")
            canvas.setStrokeColor(colors.HexColor("#e7e5e4"))
            canvas.setLineWidth(0.75)
            canvas.line(55, A4[1] - 42, A4[0] - 55, A4[1] - 42)
        canvas.restoreState()

    # Trang bìa / Tiêu đề đầu sách
    story.append(Paragraph(f"<b>{book_title}</b>", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#d79922"), spaceAfter=20))

    # 1. Gom toàn bộ các trang rời rạc lại thành một chuỗi văn bản khổng lồ duy nhất
    full_text = " ".join([page_text for page_text in book_pages if page_text])
    
    # 2. Dọn sạch toàn bộ khoảng trắng thừa, ngắt dòng rác do file gốc để lại
    full_text = re.sub(r'\s*\n\s*', ' ', full_text)
    full_text = re.sub(r'[ \t]+', ' ', full_text).strip()

    # 3. Tự động xuống dòng/tách đoạn khi gặp dấu hai chấm (:) hoặc dấu gạch ngang (-)
    # Ta dùng Regex để tìm các vị trí xuất hiện dấu ':' hoặc '-' (đầu dòng đối thoại) để ngắt đoạn thông minh
    # Biểu thức này giúp tách câu chuẩn xác mà vẫn giữ nguyên cấu trúc ngữ nghĩa
    raw_segments = re.split(r'(?<=[:])\s+|\s+(?=-\s)', full_text)

    for segment in raw_segments:
        clean_seg = segment.strip()
        if not clean_seg:
            continue
            
        # Kiểm tra nếu đoạn bắt đầu bằng dấu gạch ngang (-) thì dùng style hội thoại (thụt lề nhẹ cho đẹp)
        if clean_seg.startswith("-"):
            story.append(Paragraph(clean_seg, dialogue_style))
        else:
            story.append(Paragraph(clean_seg, body_style))

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()