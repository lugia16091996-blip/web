import os
import json
import re
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _get_service():
    # Lấy thư mục hiện tại của file push_ggsheet.py (là thư mục utils)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dùng os.path.dirname để lùi ra ngoài 1 cấp (về thư mục web/), rồi đi vào .streamlit
    json_path = os.path.join(os.path.dirname(current_dir), ".streamlit", "readbook-509104-4e0d7f4ac3c8.json")
    
    creds = Credentials.from_service_account_file(
        json_path, 
        scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

def _safe_tab_name(name: str) -> str:
    # Tên tab tối đa 100 ký tự, không được chứa [ ] * ? / \ :
    name = re.sub(r"[\[\]\*\?/\\:]", " ", name).strip()
    return (name or "Sheet1")[:100]


def push_data_to_google_sheet(df, book_title="Sách_Và_Câu_Hay"):
    try:
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        service = _get_service()
        tab = _safe_tab_name(book_title)
        tab_ref = "'" + tab.replace("'", "''") + "'"

        # Tạo tab nếu chưa có
        meta = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, fields="sheets.properties.title"
        ).execute()
        existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
        if tab not in existing:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
            ).execute()

        # Ghi đè toàn bộ tab
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=tab_ref, body={}
        ).execute()

        # to_json để chuyển numpy -> kiểu Python thuần, tránh lỗi serialize
        values = [df.columns.tolist()] + json.loads(
            df.fillna("").to_json(orient="values", force_ascii=False)
        )
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_ref}!A1",
            valueInputOption="RAW",  # RAW: câu trích bắt đầu bằng "=" không bị hiểu là công thức
            body={"values": values},
        ).execute()
        return True

    except Exception as e:
        st.error(f"Lỗi đồng bộ Google Sheets: {e}")
        return False