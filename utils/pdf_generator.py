import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Đăng ký font tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "../assets/Merriweather_24pt-Regular.ttf")

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('VietnameseFont', font_path))
    font_name = 'VietnameseFont'
else:
    font_name = 'Helvetica'

# Hàm vẽ màu nền vàng ấm cho trang PDF
def draw_warm_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#fbf7ee")) 
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.restoreState()
    
def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=50,
        topMargin=45,
        bottomMargin=45
    )
    
    story = []
        
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=15
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#9a3412"),
        spaceBefore=14,
        spaceAfter=6
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#292524")
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#78716c")
    )

    # Tiêu đề tài liệu
    story.append(Paragraph("SỔ TAY CÂU HAY & CẢM NHẬN SÂU", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#d79922"), spaceAfter=15))
    
    grouped = df_quotes.groupby("Tên sách")
    
    for book_name, group in grouped:
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#fde68a"), spaceAfter=8))
        
        for idx, row in group.iterrows():
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;{row['Trích đoạn']}&rdquo;"
            story.append(Paragraph(quote_text, content_style))
            
            if row['Lý do chọn']:
                story.append(Spacer(1, 3))
                story.append(Paragraph(f"<b>Lý do chọn:</b> {row['Lý do chọn']}", content_style))
                
            if row['Diễn đạt lại cá nhân']:
                story.append(Spacer(1, 3))
                story.append(Paragraph(f"<b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}", content_style))
                
            story.append(Spacer(1, 4))
            emotion_text = f"<b>Tầng cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            story.append(Paragraph(emotion_text, meta_style))
            
            # Thêm một đường gạch ngang nhỏ phân cách giữa các câu trích dẫn trong cùng một sách
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#fef3c7"), spaceAfter=8))
            
        story.append(Spacer(1, 10))

    doc.build(story, onFirstPage=draw_warm_background, onLaterPages=draw_warm_background)
    buffer.seek(0)
    return buffer.getvalue()