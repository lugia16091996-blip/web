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
    
    # Style cho Tên sách (đồng thời là tiêu đề lớn của cuốn sách đó)
    book_title_style = ParagraphStyle(
        'BookTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#7c2d12"), # Màu nâu đỏ trầm ấm
        spaceBefore=15,
        spaceAfter=6,
        keepWithNext=True # Đảm bảo tiêu đề luôn đi liền với dòng nội dung ngay sau nó, không bị mồ côi ở cuối trang
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

    grouped = df_quotes.groupby("Tên sách")
    
    first_book = True
    for book_name, group in grouped:
        # Nếu không phải cuốn sách đầu tiên, thêm khoảng cách ngắt giữa các sách
        if not first_book:
            story.append(Spacer(1, 15))
        first_book = False
        
        # 1. Tiêu đề chính là Tên sách
        story.append(Paragraph(f"<b>{book_name}</b>", book_title_style))
        # 2. Dấu gạch ngang thanh lịch ngay dưới tiêu đề
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d79922"), spaceAfter=10))
        
        for idx, row in group.iterrows():
            # In đậm các nhãn và nội dung theo yêu cầu
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;<b>{row['Trích đoạn']}</b>&rdquo;"
            story.append(Paragraph(quote_text, content_style))
            
            if row['Lý do chọn']:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<b>Lý do chọn:</b> {row['Lý do chọn']}", content_style))
                
            if row['Diễn đạt lại cá nhân']:
                story.append(Spacer(1, 4))
                story.append(Paragraph(f"<b>Cảm nhận cá nhân:</b> <b>{row['Diễn đạt lại cá nhân']}</b>", content_style))
                
            story.append(Spacer(1, 5))
            emotion_text = f"<b>Tầng cảm xúc:</b> <b>{row['Tầng cảm xúc']}</b> &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            story.append(Paragraph(emotion_text, meta_style))
            
            # Đường gạch ngang nhỏ mờ tinh tế phân cách giữa các trích dẫn trong cùng một sách
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#fde68a"), spaceAfter=8))

    # Xây dựng tài liệu với nền vàng ấm
    doc.build(story, onFirstPage=draw_warm_background, onLaterPages=draw_warm_background)
    buffer.seek(0)
    return buffer.getvalue()