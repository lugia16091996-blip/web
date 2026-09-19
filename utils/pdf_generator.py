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

# Hàm vẽ nền vàng ấm và Running Header cho trang ĐẦU TIÊN
fn_font_name = font_name # Biến phụ trợ cho canvas callback
def draw_first_page(canvas, doc):
    canvas.saveState()
    # 1. Vẽ màu nền vàng ấm toàn trang
    canvas.setFillColor(colors.HexColor("#fbf7ee"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()

# Hàm vẽ nền vàng ấm và Running Header cho các trang TỪ TRANG THỨ 2 TRỞ ĐI
def draw_later_pages(canvas, doc):
    canvas.saveState()
    # 1. Vẽ màu nền vàng ấm toàn trang
    canvas.setFillColor(colors.HexColor("#fbf7ee"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    
    # 2. Vẽ Running Header phía trên cùng
    canvas.setFont(fn_font_name, 8)
    canvas.setFillColor(colors.HexColor("#78716c"))
    canvas.drawString(50, A4[1] - 30, "SỔ TAY CÂU HAY & CẢM NHẬN SÂU")
    canvas.setStrokeColor(colors.HexColor("#e7e5e4"))
    canvas.setLineWidth(0.5)
    canvas.line(50, A4[1] - 35, A4[0] - 40, A4[1] - 35)
    canvas.restoreState()

def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=50,
        topMargin=55,
        bottomMargin=45
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=24,
        alignment=1,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=15
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#9a3412"),
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=16,  # Giãn dòng thoáng đãng, dễ đọc
        textColor=colors.HexColor("#292524"),
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#78716c")
    )

    # Tiêu đề mở đầu trang đầu tiên
    story.append(Paragraph("SỔ TAY CÂU HAY & CẢM NHẬN SÂU", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#d79922"), spaceAfter=15))
    
    grouped = df_quotes.groupby("Tên sách")
    
    for book_name, group in grouped:
        # Tiêu đề tên sách
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d79922"), spaceAfter=12))
        
        for idx, row in group.iterrows():
            # In đậm thông tin và trích đoạn trực tiếp, thoải mái ngắt trang
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;{row['Trích đoạn']}&rdquo;"
            story.append(Paragraph(quote_text, content_style))
            
            if row['Lý do chọn']:
                story.append(Spacer(1, 2))
                story.append(Paragraph(f"<b>Lý do chọn:</b> {row['Lý do chọn']}", content_style))
                
            if row['Diễn đạt lại cá nhân']:
                story.append(Spacer(1, 2))
                story.append(Paragraph(f"<b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}", content_style))
                
            story.append(Spacer(1, 4))
            emotion_text = f"<b>Tầng cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            story.append(Paragraph(emotion_text, meta_style))
            
            # Dấu gạch ngang `---` phân tách rõ ràng giữa các trích dẫn
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="40%", thickness=0.8, color=colors.HexColor("#d79922"), hAlign='CENTER', spaceAfter=12))
            
        story.append(Spacer(1, 10))

    # Build tài liệu và gọi callback vẽ nền + header riêng cho trang đầu và trang sau
    doc.build(story, onFirstPage=draw_first_page, onLaterPages=draw_later_pages)
    buffer.seek(0)
    return buffer.getvalue()