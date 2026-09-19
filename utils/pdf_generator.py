import io
import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    # Kiểm tra và đăng ký font tiếng Việt (hỗ trợ hiển thị có dấu chuẩn trên PDF)
    # File font này thường nằm trong thư mục assets của dự án
    font_path = os.path.join(os.path.dirname(__file__), "../assets/Merriweather_24pt-Regular.ttf")
    font_name = 'VietnameseFont' if os.path.exists(font_path) else 'Helvetica'
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('VietnameseFont', font_path))
        except Exception:
            font_name = 'Helvetica' # Fallback nếu lỗi font

    # Cấu hình lề trang giấy A4 chuẩn sổ tay
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=55,
        bottomMargin=45
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Định nghĩa các style chữ với cỡ lớn, giãn dòng rộng rãi để đọc êm mắt
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        leading=26,
        alignment=1, # Canh giữa
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=15
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        leading=20,
        textColor=colors.HexColor("#9a3412"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=20,
        textColor=colors.HexColor("#292524"),
        spaceAfter=8
    )

    # Hàm vẽ màu nền vàng ấm và thanh tiêu đề đầu trang tự động cho mọi trang PDF
    def draw_background(canvas, doc):
        canvas.saveState()
        # Tô toàn bộ nền trang bằng màu vàng ấm #fbf7ee
        canvas.setFillColor(colors.HexColor("#fbf7ee"))
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        
        # Vẽ header phía trên từ trang thứ 2 trở đi
        if canvas._pageNumber > 1:
            canvas.setFont(font_name, 9)
            canvas.setFillColor(colors.HexColor("#78716c"))
            canvas.drawString(45, A4[1] - 30, "Sổ Tay Trích Đoạn Sách & Cảm Nhận")
            canvas.setStrokeColor(colors.HexColor("#e7e5e4"))
            canvas.setLineWidth(0.75)
            canvas.line(45, A4[1] - 35, A4[0] - 45, A4[1] - 35)
        canvas.restoreState()

    # Tiêu đề chính của tài liệu PDF xuất ra
    story.append(Paragraph("<b>SỔ TAY TRÍCH ĐOẠN & CẢM NHẬN SÁCH</b>", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#d79922"), spaceAfter=15))

    # Gom nhóm theo từng cuốn sách để hiển thị gọn gàng
    if "Tên sách" in df_quotes.columns:
        grouped = df_quotes.groupby("Tên sách")
    else:
        grouped = [("Sách tổng hợp", df_quotes)]

    for book_name, group in grouped:
        story.append(Paragraph(f"📚 <b>{book_name}</b>", book_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e7e5e4"), spaceAfter=10))
        
        for idx, row in group.iterrows():
            page_num = row.get("Trang", "N/A")
            quote = row.get("Trích đoạn", "")
            reason = row.get("Lý do chọn", "")
            rephrase = row.get("Diễn đạt lại cá nhân", "")
            emotion = row.get("Tầng cảm xúc", "")
            time_val = row.get("Thời gian", "")

            # Nội dung chi tiết của từng câu trích dẫn lưu trong sổ tay
            content_html = f"""
            <b>[Trang {page_num}]</b> - <i>{emotion}</i><br/>
            <b>💬 Trích đoạn:</b> {quote}<br/>
            """
            if reason and str(reason).strip():
                content_html += f"<b>💡 Lý do chọn:</b> {reason}<br/>"
            if rephrase and str(rephrase).strip():
                content_html += f"<b>🔄 Diễn đạt lại:</b> {rephrase}<br/>"
            if time_val and str(time_val).strip():
                content_html += f"<font size='9' color='#78716c'>⏱ Lưu lúc: {time_val}</font>"

            story.append(Paragraph(content_html, body_style))
            story.append(Spacer(1, 8))

    # Build file PDF
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return buffer.getvalue()