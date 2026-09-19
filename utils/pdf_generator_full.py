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
    
    body_style = ParagraphStyle(
        'BookBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,      # Chữ lớn đọc êm mắt
        leading=26,       # Giãn dòng rộng rãi
        textColor=colors.HexColor("#292524"),
        spaceAfter=12
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

    # 3. Tách văn bản thành các đoạn văn chuẩn dựa vào dấu chấm câu hoặc cấu trúc đoạn (nếu có xuống dòng đôi)
    # Hoặc để hệ thống tự dàn đều thành các đoạn văn mượt mà
    paragraphs = [p.strip() for p in full_text.split('.') if p.strip()]

    # Ghép lại các câu thành đoạn văn hoàn chỉnh để chữ chảy dài liên tục, không bị ngắt trang ngang xương
    current_chunk = ""
    for para in paragraphs:
        sentence = para + "."
        if len(current_chunk) + len(sentence) < 800: # Gom các câu thành từng khối vừa đủ để dàn trang đẹp mắt
            current_chunk += " " + sentence
        else:
            if current_chunk.strip():
                story.append(Paragraph(current_chunk.strip(), body_style))
            current_chunk = sentence
            
    if current_chunk.strip():
        story.append(Paragraph(current_chunk.strip(), body_style))

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()