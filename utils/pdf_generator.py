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

# Biến phụ trợ cho canvas callback
fn_font_name = font_name 

def draw_first_page(canvas, doc):
    canvas.saveState()
    # 1. Vẽ màu nền vàng ấm toàn trang
    canvas.setFillColor(colors.HexColor("#fbf7ee"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()

def draw_later_pages(canvas, doc):
    canvas.saveState()
    # 1. Vẽ màu nền vàng ấm toàn trang
    canvas.setFillColor(colors.HexColor("#fbf7ee"))
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    
    # 2. Vẽ Running Header phía trên cùng
    canvas.setFont(fn_font_name, 9)
    canvas.setFillColor(colors.HexColor("#78716c"))
    canvas.drawString(55, A4[1] - 35, "SỔ TAY CỦA BẠN - SUY NGHĨ CỦA BẠN")
    canvas.setStrokeColor(colors.HexColor("#e7e5e4"))
    canvas.setLineWidth(0.75)
    canvas.line(55, A4[1] - 42, A4[0] - 55, A4[1] - 42)
    canvas.restoreState()

def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    # Mở rộng lề sang hai bên (left/right = 55) để trang giấy gọn gàng, không bị bè ra quá rộng
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
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=22,
        leading=30,
        alignment=1,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=20
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        leading=24,
        textColor=colors.HexColor("#9a3412"),
        spaceBefore=25,
        spaceAfter=12,
        keepWithNext=True
    )
    
    # TĂNG MẠNH CỠ CHỮ VÀ KHOẢNG CÁCH DÒNG (Rất thoáng, không bao giờ bị khít)
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,      # Cỡ chữ rất lớn, đọc cực kỳ dễ chịu
        leading=26,       # Giãn chiều cao dòng thênh thang
        textColor=colors.HexColor("#292524"),
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=20,
        textColor=colors.HexColor("#78716c")
    )

    # Tiêu đề mở đầu trang đầu tiên
    story.append(Paragraph("SỔ TAY CÂU HAY & CẢM NHẬN SÂU", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#d79922"), spaceAfter=20))
    
    grouped = df_quotes.groupby("Tên sách")
    
    for book_name, group in grouped:
        # Tiêu đề tên sách
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#d79922"), spaceAfter=16))
        
        for idx, row in group.iterrows():
            # Trích đoạn to rõ, giãn dòng siêu thoáng
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;{row['Trích đoạn']}&rdquo;"
            story.append(Paragraph(quote_text, content_style))
            
            if row['Lý do chọn']:
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Lý do chọn:</b> {row['Lý do chọn']}", content_style))
                
            if row['Diễn đạt lại cá nhân']:
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}", content_style))
                
            story.append(Spacer(1, 8))
            emotion_text = f"<b>Tầng cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            story.append(Paragraph(emotion_text, meta_style))
            
            # Dấu gạch ngang `---` phân tách rộng rãi giữa các trích dẫn
            story.append(Spacer(1, 16))
            story.append(HRFlowable(width="50%", thickness=1, color=colors.HexColor("#d79922"), hAlign='CENTER', spaceAfter=20))
            
        story.append(Spacer(1, 20))

    doc.build(story, onFirstPage=draw_first_page, onLaterPages=draw_later_pages)
    buffer.seek(0)
    return buffer.getvalue()
#test
