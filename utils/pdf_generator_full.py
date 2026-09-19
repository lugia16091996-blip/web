import io
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def clean_text_block(text):
    """Hàm làm sạch văn bản: xóa khoảng trắng thừa, gom dòng gãy khúc thành đoạn chuẩn"""
    if not text:
        return ""
    # Thay thế các dạng xuống dòng kèm khoảng trắng xung quanh bằng một khoảng trắng đơn
    cleaned = re.sub(r'\s*\n\s*', ' ', text)
    # Gom nhiều khoảng trắng liền nhau thành 1 khoảng trắng duy nhất
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()

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
    
    # Cỡ chữ to, giãn dòng thênh thang để bảo vệ mắt
    body_style = ParagraphStyle(
        'BookBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,      # Chữ lớn đọc êm mắt
        leading=26,       # Giãn dòng rộng rãi
        textColor=colors.HexColor("#292524"),
        spaceAfter=10     # Khoảng cách giữa các đoạn vừa phải, không bị thưa quá
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

    # Duyệt qua từng trang được bóc tách từ file sách gốc
    for idx, page_content in enumerate(book_pages):
        story.append(Paragraph(f"<b>--- Trang {idx + 1} ---</b>", ParagraphStyle('PageHeading', parent=body_style, fontSize=11, textColor=colors.HexColor("#9a3412"), spaceAfter=6)))
        
        # Tách trang theo đoạn văn thô, sau đó chạy hàm làm sạch (clean_text_block)
        paragraphs = page_content.split('\n')
        for para in paragraphs:
            cleaned_para = clean_text_block(para)
            if cleaned_para:
                story.append(Paragraph(cleaned_para, body_style))
        
        # Ngắt trang giữa các trang sách
        story.append(PageBreak())

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()