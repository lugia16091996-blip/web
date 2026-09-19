import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Đăng ký font tiếng Việt
font_path = os.path.join(os.path.dirname(__file__), "../assets/Merriweather_24pt-Regular.ttf")

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('VietnameseFont', font_path))
    font_name = 'VietnameseFont'
else:
    font_name = 'Helvetica'

# Lớp canvas tùy chỉnh để tự động in Header (Tiêu đề sách) lặp lại ở các trang sau
class BookCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # Vẽ nền và header lặp lại cho từng trang
        num_pages = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_background_and_header()
            super().showPage()
        super().save()

    def draw_background_and_header(self):
        self.saveState()
        # 1. Vẽ màu nền vàng ấm toàn trang
        self.setFillColor(colors.HexColor("#fbf7ee"))
        self.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        
        # 2. Nếu là từ trang thứ 2 trở đi, vẽ Running Header ở phía trên cùng
        if self._pageNumber > 1:
            self.setFont(font_name, 8)
            self.setFillColor(colors.HexColor("#78716c"))
            # Tiêu đề nhỏ phía trên góc trái
            self.drawString(50, A4[1] - 30, "SỔ TAY CÂU HAY & CẢM NHẬN SÂU")
            # Đường kẻ mỏng dưới header
            self.setStrokeColor(colors.HexColor("#e7e5e4"))
            self.setLineWidth(0.5)
            self.line(50, A4[1] - 35, A4[0] - 40, A4[1] - 35)
            
        self.restoreState()

def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    # Tăng topMargin lên một chút để tránh bị đè vào header ở trang sau
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
    
    # Định nghĩa các Style với leading (khoảng cách dòng) thoáng đãng, dễ đọc
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
        spaceAfter=8,
        keepWithNext=True
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=16,  # Tăng khoảng cách dòng giúp chữ không bị dính vào nhau
        textColor=colors.HexColor("#292524"),
        spaceAfter=6
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
        # Tiêu đề tên sách mỗi khi chuyển sách
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d79922"), spaceAfter=10))
        
        for idx, row in group.iterrows():
            # Gom nội dung từng trích dẫn vào một danh sách để đóng khung Table thoáng đãng
            cell_content = []
            
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;{row['Trích đoạn']}&rdquo;"
            cell_content.append(Paragraph(quote_text, content_style))
            
            if row['Lý do chọn']:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(f"<b>Lý do chọn:</b> {row['Lý do chọn']}", content_style))
                
            if row['Diễn đạt lại cá nhân']:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(f"<b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}", content_style))
                
            cell_content.append(Spacer(1, 4))
            emotion_text = f"<b>Tầng cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            cell_content.append(Paragraph(emotion_text, meta_style))
            
            # Đóng từng trích dẫn vào Table có nền vàng kem nhạt và đường gạch ngang `---` phân tách
            quote_table = Table([[cell_content]], colWidths=[500])
            quote_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")), # Nền vàng ấm nhạt cho khung
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#fde68a")),      # Viền vàng ấm
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            
            story.append(quote_table)
            # Thêm đường gạch ngang `---` nhỏ phân tách giữa các trích dẫn cho dễ nhìn
            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="30%", thickness=0.8, color=colors.HexColor("#d79922"), hAlign='CENTER', spaceAfter=10))
            
        story.append(Spacer(1, 10))

    # Xây dựng tài liệu với lớp canvas tùy chỉnh để lặp lại header tự động
    doc.build(story, canvasmaker=BookCanvas)
    buffer.seek(0)
    return buffer.getvalue()