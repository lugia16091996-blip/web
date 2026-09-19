import io
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def clean_and_format_page(page_text):
    """
    Hàm làm sạch toàn diện trang sách:
    - Gom các dòng bị đứt quãng (do ngắt dòng cứng trong file gốc) thành một khối văn bản liền mạch.
    - Xóa khoảng trắng thừa.
    - Tách lại thành các đoạn văn chuẩn dựa trên dấu xuống dòng đôi hoặc dấu chấm kết câu kết hợp khoảng trắng lớn.
    """
    if not page_text:
        return []
        
    # 1. Thay thế các ký tự xuống dòng kèm khoảng trắng xung quanh bằng một khoảng trắng đơn 
    # để nối các từ bị bẻ đôi ở cuối dòng (ví dụ: "hai\n bên" -> "hai bên")
    unified_text = re.sub(r'\s*\n\s*', ' ', page_text)
    
    # 2. Chuẩn hóa tất cả các khoảng trắng kép, tab thành 1 khoảng trắng duy nhất
    unified_text = re.sub(r'[ \t]+', ' ', unified_text).strip()
    
    # 3. Nếu sách gốc có phân chia đoạn bằng khoảng trắng đôi hoặc ký tự đặc biệt, ta có thể tách đoạn.
    # Trong trường hợp các trang sách là một khối văn bản liền, ta gom nó thành các đoạn văn hợp lý.
    # Ở đây ta sẽ chia nhỏ trang sách thành các đoạn văn nếu gặp dấu xuống dòng gốc (nếu có giữ lại cấu trúc paragraph) hoặc chia theo độ dài/dấu chấm.
    paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
    
    if not paragraphs:
        # Nếu không tìm thấy ngắt đoạn đôi, ta coi toàn bộ trang là một hoặc vài đoạn mượt mà
        paragraphs = [unified_text]
    else:
        # Làm sạch từng đoạn nhỏ sau khi chia
        cleaned_paragraphs = []
        for p in paragraphs:
            clean_p = re.sub(r'\s*\n\s*', ' ', p)
            clean_p = re.sub(r'[ \t]+', ' ', clean_p).strip()
            if clean_p:
                cleaned_paragraphs.append(clean_p)
        paragraphs = cleaned_paragraphs
        
    return paragraphs

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
        spaceAfter=12     # Khoảng cách giữa các đoạn
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
        
        # Xử lý làm sạch toàn bộ trang sách, nối liền các dòng bị ngắt cụt
        formatted_paragraphs = clean_and_format_page(page_content)
        
        for para in formatted_paragraphs:
            story.append(Paragraph(para, body_style))
        
        # Ngắt trang giữa các trang sách
        story.append(PageBreak())

    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()