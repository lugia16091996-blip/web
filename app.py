import pandas as pd
import streamlit as st
from utils.document_processor import (
    parse_docx_to_pages,
    parse_epub_to_pages,
    parse_pdf_to_pages,
    parse_txt_to_pages,
)
from utils.storage_manager import convert_df_to_excel, init_session_state
from utils.tts_player import render_tts_player , render_audio_section
from utils.push_ggsheet import push_data_to_google_sheet  
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
st.subheader(
    "📁 Tải lên tài liệu (Hỗ trợ: .epub, .pdf thuần text, .txt, .docx)"
)
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

        # Phân loại và gọi đúng hàm tương ứng đã viết ở file xử lý
        if file_name.endswith(".epub"):
          st.session_state.book_pages = parse_epub_to_pages(uploaded_file)
        elif file_name.endswith(".pdf"):
          st.session_state.book_pages = parse_pdf_to_pages(uploaded_file)
        elif file_name.endswith(".txt"):
          st.session_state.book_pages = parse_txt_to_pages(uploaded_file)
        elif file_name.endswith(".docx"):
          st.session_state.book_pages = parse_docx_to_pages(uploaded_file)

        st.session_state.current_file_name = uploaded_file.name
        st.success(
            f"Đã nạp xong file '{uploaded_file.name}' tổng cộng"
            f" {len(st.session_state.book_pages)} trang!"
        )

      except ValueError as e:
        # Bắt lỗi nếu PDF là file scan
        st.error(f"⚠️ {e}")
      except Exception as e:
        st.error(f"⚠️ Đã xảy ra lỗi khi đọc file: {e}")
        
# 2. Chọn trang thông minh (Tự động giới hạn tối đa 2 trang để tối ưu cho Mobile)

if len(st.session_state.book_pages) > 0:
  total_pages = len(st.session_state.book_pages)
  page_list = list(range(1, total_pages + 1))

  # Khởi tạo biến trạng thái trang hiện tại nếu chưa có
  if "current_page" not in st.session_state:
    st.session_state.current_page = 1

  # Đảm bảo giới hạn không vượt quá tổng số trang
  if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages

  st.markdown("---")
  st.subheader("📖 Chọn trang bắt đầu (Đọc tự động 2 trang)")

  # CÁCH FIX: Sử dụng hàm callback khi thay đổi selectbox để cập nhật current_page an toàn
  def update_page_from_selectbox():
    st.session_state.current_page = st.session_state.select_from_page_box

  # Dùng index tương ứng với current_page hiện tại
  current_index = st.session_state.current_page - 1

  from_page = st.selectbox(
      "Từ trang số:",
      page_list,
      index=current_index,
      key="select_from_page_box",
      on_change=update_page_from_selectbox,
  )

  # Đồng bộ lại biến from_page với current_page
  from_page = st.session_state.current_page

  # Tự động tính trang kết thúc (giới hạn tối đa 2 trang cho Mobile)
  to_page = min(from_page + 1, total_pages)

  # Gom nội dung của 2 trang này lại
  active_reading_content = ""
  start_idx = max(0, from_page - 1)
  end_idx = min(total_pages, to_page)

  for p in range(start_idx, end_idx):
    active_reading_content += (
        f"\n[Trang {p+1}]\n" + st.session_state.book_pages[p]
    )

  st.markdown(
      f"🔍 **Nội dung hiển thị (Tự động lấy từ Trang {from_page} đến Trang"
      f" {to_page}):**"
  )
  dynamic_text_key = f"editable_reading_box_{from_page}_{to_page}"

  # CSS tùy chỉnh font và cỡ chữ
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


# 3 & 4. GỌI TRÌNH PHÁT AUDIO VÀ NÚT CHUYỂN TRANG (ĐÃ ĐƯỢC GÓI GỌN TRONG MODULE)
  render_audio_section(edited_reading_content, total_pages)



  # 5. Khu vực lưu câu hay
  st.markdown("---")
  st.subheader("✍️ Lưu lại câu hay & Số trang tương ứng")
  with st.form("quote_form"):
    quote_input = st.text_area(
        "Nhập hoặc dán câu tâm đắc vừa nghe vào đây:",
        value="",
        placeholder="Ví dụ: Đời ngắn đừng ngủ dài...",
    )
    recorded_page = st.number_input(
        "Số trang đang đọc khi gặp câu này:",
        min_value=from_page,
        max_value=to_page,
        value=from_page,
    )
    note_id = st.text_input(
        "Ghi chú cá nhân (nếu có):", placeholder="Bài học rút ra..."
    )
    submitted = st.form_submit_button("💾 Lưu vào bộ nhớ")

    if submitted and quote_input:
      st.session_state.saved_quotes.append({
          "Trang số": recorded_page,
          "Câu nói / Đoạn hay": quote_input,
          "Ghi chú": note_id,
          "Thời gian": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
      })
      st.success(f"Đã lưu câu hay ở Trang {recorded_page} thành công!")


# 6. Hiển thị danh sách và xuất Excel / Push Google Sheets (Chỉ giữ lại 1 khối duy nhất này)
if st.session_state.saved_quotes:
    st.markdown("---")
    st.subheader(f"📋 Danh sách câu hay đã lưu ({len(st.session_state.saved_quotes)} câu)")

    df_quotes = pd.DataFrame(st.session_state.saved_quotes)
    df_quotes = df_quotes.sort_values(by="Trang số")
    st.dataframe(df_quotes, use_container_width=True)

    st.markdown("---")
    st.subheader("📥 Xuất dữ liệu & Đồng bộ")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        excel_data = convert_df_to_excel(df_quotes)
        st.download_button(
            label="📊 Tải xuống file Excel (.xlsx)",
            data=excel_data,
            file_name="sach_va_cau_hay.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_download_excel_quotes"  # <--- Thêm key này vào để chống trùng lặp ID tuyệt đối
        )
        
    with col_s2:
        # Trong khối nút đẩy dữ liệu
        if st.button("☁️ Đẩy dữ liệu lên Google Sheets", use_container_width=True):
            with st.spinner("Đang đồng bộ lên Google Sheets..."):
                book_title = st.session_state.get("current_file_name", "Sách").rsplit(".", 1)[0]
                if push_data_to_google_sheet(df_quotes, book_title):
                    st.success("Đồng bộ dữ liệu lên Google Sheets thành công! 🎉")