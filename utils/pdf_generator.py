import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
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

# Lớp canvas thông minh để tự động nhận diện và in Tên Sách tương ứng ở Header từng trang
class BookHeaderCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # Lần chạy thứ 2: Vẽ background và header động cho từng trang
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
        
        # 2. Running Header ở trang 2 trở đi (Hiển thị tiêu đề sách động)
        if self._pageNumber > 1:
            self.setFont(font_name, 9)
            self.setFillColor(colors.HexColor("#78716c"))
            
            # Lấy tên sách tương ứng từ thuộc tính được lưu trong canvas trên từng trang
            book_title_header = getattr(self, '_current_book_title', 'SỔ TAY CÂU HAY & CẢM NHẬN SÂU')
            self.drawString(55, A4[1] - 35, f"Sách: {book_title_header}")
            
            self.setStrokeColor(colors.HexColor("#e7e5e4"))
            self.setLineWidth(0.75)
            self.line(55, A4[1] - 42, A4[0] - 55, A4[1] - 42)
            
        self.restoreState()

def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
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
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=15,      # Cỡ chữ lớn, đọc êm mắt
        leading=26,       # Giãn dòng thênh thang
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
        # Hàm callback đánh dấu tên sách cho trang hiện tại khi build flowable
        def set_book_canvas_title(canvas, doc, title=book_name):
            canvas._current_book_title = title

        # Chèn đoạn flowable trong suốt để cập nhật tiêu đề sách vào canvas theo từng trang chảy văn bản
        from reportlab.platypus import Macro
        story.append(Macro(f"self._current_book_title = {repr(book_name)}"))

        # Tiêu đề tên sách hiển thị trong nội dung
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#d79922"), spaceAfter=16))
        
        for idx, row in group.iterrows():
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
            
            story.append(Spacer(1, 16))
            story.append(HRFlowable(width="50%", thickness=1, color=colors.HexColor("#d79922"), hAlign='CENTER', spaceAfter=20))
            
        story.append(Spacer(1, 20))

    # Sử dụng BookHeaderCanvas để tự động nhận diện tiêu đề sách ở header từng trang
    doc.build(story, canvasmaker=BookHeaderCanvas)
    buffer.seek(0)
    return buffer.getvalue()