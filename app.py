import pandas as pd
import streamlit as st
import unicodedata
import re

from utils.document_processor import (
    parse_docx_to_pages,
    parse_epub_to_pages,
    parse_pdf_to_pages,
    parse_txt_to_pages,
)
from utils.storage_manager import convert_df_to_excel, init_session_state
from utils.tts_player import render_audio_section, render_tts_player
from utils.push_ggsheet import push_data_to_google_sheet  
from utils.pdf_generator import generate_quotes_pdf

# Cấu hình tiêu đề trang web
st.set_page_config(
    page_title="Text to speech and notebook", page_icon="📚", layout="centered"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&display=swap');

    div[data-baseweb="textarea"] textarea {
        font-family: 'Merriweather', serif !important;
        font-size: 30px !important;
        line-height: 2.1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎧 Text to speech and notebook")
st.write("Đọc văn bản theo Trang - Chọn Dropdown cập nhật tức thì - Lưu Excel.")

# Khởi tạo session
init_session_state()

# 1. Khu vực upload file tài liệu tổng hợp
st.subheader("📁 Tải lên tài liệu (Hỗ trợ: .epub, .pdf thuần text, .txt, .docx)")
uploaded_file = st.file_uploader(
    "Chọn file sách:",
    type=["epub", "pdf", "txt", "docx"],
    key="document_uploader",
)

if uploaded_file is not None:
    if (
        "current_file_name" not in st.session_state
        or st.session_state.current_file_name != uploaded_file.name
    ):
        with st.spinner("Đang bóc tách và chia trang sách, chờ xíu nha..."):
            try:
                file_name = uploaded_file.name.lower()

                if file_name.endswith(".epub"):
                    st.session_state.book_pages = parse_epub_to_pages(uploaded_file)
                elif file_name.endswith(".pdf"):
                    st.session_state.book_pages = parse_pdf_to_pages(uploaded_file)
                elif file_name.endswith(".txt"):
                    st.session_state.book_pages = parse_txt_to_pages(uploaded_file)
                elif file_name.endswith(".docx"):
                    st.session_state.book_pages = parse_docx_to_pages(uploaded_file)

                st.session_state.current_file_name = uploaded_file.name
                st.success(f"Đã nạp xong file '{uploaded_file.name}' tổng cộng {len(st.session_state.book_pages)} trang!")

            except ValueError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"⚠️ Đã xảy ra lỗi khi đọc file: {e}")
        
# 2. Chọn trang thông minh
if len(st.session_state.book_pages) > 0:
    total_pages = len(st.session_state.book_pages)
    page_list = list(range(1, total_pages + 1))

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages

    st.markdown("---")
    st.subheader("📖 Chọn trang bắt đầu (Đọc tự động 2 trang)")

    def update_page_from_selectbox():
        st.session_state.current_page = st.session_state.select_from_page_box

    current_index = st.session_state.current_page - 1

    from_page = st.selectbox(
        "Từ trang số:",
        page_list,
        index=current_index,
        key="select_from_page_box",
        on_change=update_page_from_selectbox,
    )

    from_page = st.session_state.current_page
    to_page = min(from_page + 1, total_pages)

    active_reading_content = ""
    start_idx = max(0, from_page - 1)
    end_idx = min(total_pages, to_page)

    for p in range(start_idx, end_idx):
        active_reading_content += f"\n[Trang {p+1}]\n" + st.session_state.book_pages[p]

    st.markdown(f"🔍 **Nội dung hiển thị (Tự động lấy từ Trang {from_page} đến Trang {to_page}):**")
    dynamic_text_key = f"editable_reading_box_{from_page}_{to_page}"

    st.markdown(
        """
        <style>
        .stTextArea textarea {
            font-family: 'Merriweather', serif !important;
            font-size: 26px !important;
            line-height: 1.8 !important;
        }
        .stTextArea label {
            font-size: 22px !important;
            font-weight: bold !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    edited_reading_content = st.text_area(
        "Khung chỉnh sửa nội dung đọc:",
        value=active_reading_content,
        height=500,
        key=dynamic_text_key,
    )

    # 3 & 4. GỌI TRÌNH PHÁT AUDIO VÀ NÚT CHUYỂN TRANG
    render_audio_section(edited_reading_content, total_pages)

# Tự động lấy tên sách từ file đang upload (nếu có)
default_book_name = ""
if "current_file_name" in st.session_state:
    default_book_name = st.session_state.current_file_name.rsplit(".", 1)[0]

# 5. Khu vực lưu câu hay
st.markdown("---")
st.subheader("✍️ Lưu lại câu hay & Cảm nhận sâu")

with st.form("quote_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        book_name = st.text_input(
            "📚 Tên sách:",
            value=default_book_name,
            placeholder="Nhập tên cuốn sách bạn đang đọc...",
        )
    with col2:
        recorded_page = st.number_input(
            "📖 Trang số:",
            min_value=1,
            max_value=len(st.session_state.book_pages) if len(st.session_state.book_pages) > 0 else 1000,
            value=st.session_state.get("current_page", 1),
        )

    quote_input = st.text_area(
        "💬 Trích đoạn gốc:",
        value="",
        placeholder="Nhập hoặc dán câu / đoạn văn tâm đắc vào đây...",
        height=100,
    )

    col3, col4 = st.columns(2)
    with col3:
        reason_input = st.text_area(
            "💡 Lý do chọn câu này:",
            placeholder="Tại sao câu này lại thu hút bạn?",
            height=100,
        )
    with col4:
        rephrase_input = st.text_area(
            "🔄 Diễn đạt lại theo ý cá nhân:",
            placeholder="Tóm tắt hoặc viết lại bằng vốn từ của chính bạn...",
            height=100,
        )

    emotion_level = st.select_slider(
        "🎭 Tầng cảm xúc khi đọc / nghe:",
        options=[
            "🌱 Bình thản",
            "🤔 Suy ngẫm",
            "💡 Chạm / Thức tỉnh",
            "🔥 Truyền cảm hứng",
            "❤️ Súc động sâu sắc",
        ],
        value="💡 Chạm / Thức tỉnh",
    )

    submitted = st.form_submit_button("💾 Lưu vào bộ nhớ")

    if submitted:
        if not quote_input.strip():
            st.warning("⚠️ Vui lòng nhập nội dung trích đoạn trước khi lưu!")
        else:
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

            st.session_state.saved_quotes.append({
                "Tên sách": book_name if book_name else "Chưa rõ tên sách",
                "Trang": recorded_page,
                "Trích đoạn": quote_input,
                "Lý do chọn": reason_input,
                "Diễn đạt lại cá nhân": rephrase_input,
                "Tầng cảm xúc": emotion_level,
                "Thời gian": current_time,
            })
            st.success(f"✅ Đã lưu thành công câu hay trong cuốn **'{book_name}'** (Trang {recorded_page})!")

# 6. Hiển thị danh sách và xuất dữ liệu theo thứ tự dọc từ trên xuống
if st.session_state.saved_quotes:
    st.markdown("---")
    st.subheader(f"📋 Danh sách câu hay đã lưu ({len(st.session_state.saved_quotes)} câu)")

    df_quotes = pd.DataFrame(st.session_state.saved_quotes)
    df_quotes = df_quotes.sort_values(by="Trang")
    st.dataframe(df_quotes, use_container_width=True)

    st.markdown("---")
    st.subheader("📥 Xuất dữ liệu & Đồng bộ")

    # Chuẩn bị tên file động & thời gian
    time_str = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").strftime("%Y%m%d_%H%M%S")
    current_book = st.session_state.get("current_file_name", "sach").rsplit(".", 1)[0]
    
    nfkd_form = unicodedata.normalize('NFKD', current_book)
    no_accent_book = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    safe_book_name = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in no_accent_book)
    safe_book_name = re.sub(r'[\s_]+', '_', safe_book_name).strip('_')[:50]

    # THỨ TỪ NÚT BẤM DỌC TỪ TRÊN XUỐNG:

    # 1. Tải xuống file Excel
    excel_data = convert_df_to_excel(df_quotes)
    dynamic_file_name = f"{time_str}_{safe_book_name}_notebook.xlsx"
    st.download_button(
        label="📊 Tải xuống file Excel (.xlsx)",
        data=excel_data,
        file_name=dynamic_file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_excel_quotes",
        use_container_width=True
    )
    
    # 2. Đẩy dữ liệu lên Google Sheets
    if st.button("☁️ Đẩy dữ liệu lên Google Sheets", use_container_width=True, key="btn_push_ggsheet"):
        with st.spinner("Đang đồng bộ lên Google Sheets..."):
            book_title = st.session_state.get("current_file_name", "Sách").rsplit(".", 1)[0]
            if push_data_to_google_sheet(df_quotes, book_title):
                st.success("Đồng bộ dữ liệu lên Google Sheets thành công! 🎉\n\nLink lưu trữ: https://docs.google.com/spreadsheets/d/1-KdWo05lCdwLFGogWexM6oGc7IKSXtVOvDZSWj0u1n0/edit?gid=529665069#gid=529665069")

    # 3. Tải PDF chuẩn A4
    pdf_data = generate_quotes_pdf(df_quotes)
    pdf_file_name = f"{time_str}_so_tay_cau_hay.pdf"
    st.download_button(
        label="📄 Tải PDF chuẩn A4",
        data=pdf_data,
        file_name=pdf_file_name,
        mime="application/pdf",
        key="btn_download_pdf_quotes",
        use_container_width=True
    )
    
    # 4. Xóa sạch dữ liệu đọc cuốn tiếp theo
    if st.button("🗑️ Xóa sạch danh sách để đọc cuốn tiếp theo", use_container_width=True, key="btn_clear_all_quotes"):
        st.session_state.saved_quotes = []
        st.session_state.book_pages = []
        st.session_state.current_page = 1
        st.rerun()

    # Kiểm tra nếu đã upload sách và có dữ liệu phân trang
    if len(st.session_state.book_pages) > 0:
        st.markdown("---")
        st.subheader("📚 Xuất toàn bộ nội dung sách ra PDF (Nền vàng ấm, Chữ to)")
        
        from utils.pdf_generator import generate_full_book_pdf
        
        # Lấy tên sách sạch từ file đang upload
        current_book_name = st.session_state.get("current_file_name", "sach").rsplit(".", 1)[0]
        
        if st.button("✨ Gen lại toàn bộ cuốn sách thành PDF chữ to", use_container_width=True):
            with st.spinner("Đang tổng hợp toàn bộ các trang sách và dựng file PDF, chờ chút xíu nha..."):
                full_pdf_bytes = generate_full_book_pdf(st.session_state.book_pages, current_book_name)
                
                st.success("Đã gen xong toàn bộ cuốn sách thành công!")
                st.download_button(
                    label="📥 Tải xuống file PDF toàn văn (Đọc cực êm mắt)",
                    data=full_pdf_bytes,
                    file_name=f"{current_book_name}_toan_van_chu_to.pdf",
                    mime="application/pdf",
                    key="btn_download_full_book_pdf"
                )