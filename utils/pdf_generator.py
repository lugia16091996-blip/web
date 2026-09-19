import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
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

# Hàm vẽ màu nền vàng ấm cho từng trang giấy PDF
def draw_warm_background(canvas, doc):
    canvas.saveState()
    # Mã màu vàng kem ấm áp (Warm Cream/Sepia)
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
        textColor=colors.HexColor("#7c2d12"), # Đổi màu chữ tiêu đề sang nâu đỏ trầm ấm
        spaceAfter=15
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#9a3412"), # Tên sách màu cam đất/nâu ấm
        spaceBefore=12,
        spaceAfter=6
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#292524") # Chữ màu nâu đen dịu mắt thay vì đen tuyền
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#78716c") # Màu xám nâu cho phần meta (thời gian, cảm xúc)
    )

    # Tiêu đề tài liệu
    story.append(Paragraph("SỔ TAY CÂU HAY & CẢM NHẬN SÂU", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#d79922"), spaceAfter=15))
    
    grouped = df_quotes.groupby("Tên sách")
    
    for book_name, group in grouped:
        story.append(Paragraph(f"Tên sách: {book_name}", book_header_style))
        
        for idx, row in group.iterrows():
            quote_text = f"<b>Trang {row['Trang']}:</b> &ldquo;{row['Trích đoạn']}&rdquo;"
            reason_text = f"<b>Lý do chọn:</b> {row['Lý do chọn']}" if row['Lý do chọn'] else ""
            rephrase_text = f"<b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}" if row['Diễn đạt lại cá nhân'] else ""
            emotion_text = f"<b>Tầng cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; <i>{row['Thời gian']}</i>"
            
            cell_content = [
                Paragraph(quote_text, content_style),
            ]
            if reason_text:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(reason_text, content_style))
            if rephrase_text:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(rephrase_text, content_style))
                
            cell_content.append(Spacer(1, 5))
            cell_content.append(Paragraph(emotion_text, meta_style))
            
            quote_table = Table([[cell_content]], colWidths=[500])
            quote_table.setStyle(TableStyle([
                # Đổi màu nền khung từng câu thành màu vàng kem đậm hơn nền trang một chút để tạo chiều sâu
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")), 
                # Viền khung màu nâu nhạt ấm áp
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#fde68a")), 
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            
            story.append(quote_table)
            story.append(Spacer(1, 10))
            
        story.append(Spacer(1, 10))

    # Truyền hàm vẽ nền vàng ấm vào hàm build thông qua tham số onFirstPage và onLaterPages
    doc.build(story, onFirstPage=draw_warm_background, onLaterPages=draw_warm_background)
    buffer.seek(0)
    return buffer.getvalue()