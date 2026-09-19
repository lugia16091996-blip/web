import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1. Đăng ký font tiếng Việt một lần duy nhất khi load module
# Trỏ chuẩn xác vào thư mục assets bên cạnh file script hiện tại
font_path = os.path.join(os.path.dirname(__file__), "../assets/Merriweather_24pt-Regular.ttf")

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('VietnameseFont', font_path))
    font_name = 'VietnameseFont'
else:
    # Fallback nếu vô tình quên bỏ file vào assets
    font_name = 'Helvetica'
    
def generate_quotes_pdf(df_quotes):
    buffer = io.BytesIO()
    
    # Thiết lập trang A4, lề chuẩn để đóng gáy (lề trái rộng hơn chút: 50pt, các lề khác 40pt)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=50,
        topMargin=45,
        bottomMargin=45
    )
    
    story = []
        
    # Định nghĩa Styles sử dụng đúng font_name đã đăng ký phía trên
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        alignment=1, # Canh giữa
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=15
    )
    
    book_header_style = ParagraphStyle(
        'BookHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=10,
        spaceAfter=5
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )

    # Tiêu đề tài liệu
    story.append(Paragraph("📖 SỔ TAY CÂU HAY & CẢM NHẬN SÂU", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f766e"), spaceAfter=15))
    
    # Gom nhóm theo Tên sách
    grouped = df_quotes.groupby("Tên sách")
    
    for book_name, group in grouped:
        story.append(Paragraph(f"📚 Sách: {book_name}", book_header_style))
        
        for idx, row in group.iterrows():
            # Tạo bảng thông tin cho từng câu hay để đóng khung gọn gàng
            quote_text = f"<b>Trang {row['Trang']}:</b> \"{row['Trích đoạn']}\""
            reason_text = f"💡 <b>Lý do chọn:</b> {row['Lý do chọn']}" if row['Lý do chọn'] else ""
            rephrase_text = f"🔄 <b>Cảm nhận cá nhân:</b> {row['Diễn đạt lại cá nhân']}" if row['Diễn đạt lại cá nhân'] else ""
            emotion_text = f"🎭 <b>Cảm xúc:</b> {row['Tầng cảm xúc']} &nbsp;&nbsp;|&nbsp;&nbsp; ⏰ <i>{row['Thời gian']}</i>"
            
            cell_content = [
                Paragraph(quote_text, content_style),
            ]
            if reason_text:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(reason_text, content_style))
            if rephrase_text:
                cell_content.append(Spacer(1, 4))
                cell_content.append(Paragraph(rephrase_text, content_style))
                
            cell_content.append(Spacer(1, 4))
            cell_content.append(Paragraph(emotion_text, meta_style))
            
            # Đóng vào Table khung bo viền
            quote_table = Table([[cell_content]], colWidths=[500])
            quote_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            
            story.append(quote_table)
            story.append(Spacer(1, 10))
            
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()