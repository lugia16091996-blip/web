import io
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def init_session_state():
    if "saved_quotes" not in st.session_state:
        st.session_state.saved_quotes = []
    if "book_pages" not in st.session_state:
        st.session_state.book_pages = []

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="CauHay")
    return output.getvalue()

# 💡 TÍCH HỢP GOOGLE SHEETS
def push_data_to_google_sheet(df):
    """Đẩy danh sách câu hay lên Google Sheets thông qua Service Account"""
    try:
        # Khai báo quyền truy cập
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Đọc thông tin xác thực từ tệp secrets của Streamlit hoặc file json cục bộ
        # Khuyên dùng: Lưu cấu hình trong .streamlit/secrets.toml
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        else:
            # Hoặc đọc file json trực tiếp nếu bạn đặt trong thư mục dự án
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
            
        client = gspread.authorize(creds)
        
        # Mở Google Sheet (Bạn cần tạo sẵn một Google Sheet và chia sẻ quyền Editor cho email của Service Account)
        sheet_name = "Book_Quotes_Manager" # Tên file Google Sheets của bạn
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.get_worksheet(0) # Lấy sheet đầu tiên
        
        # Xóa dữ liệu cũ và ghi dữ liệu mới từ DataFrame vào
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Lỗi khi đồng bộ lên Google Sheets: {e}")
        return False