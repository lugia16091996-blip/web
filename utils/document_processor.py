import re
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from docx import Document
from pypdf import PdfReader


# --- 1. HÀM LÀM SẠCH VÀ CẮT TRANG CHUNG ---
def clean_text_advanced(text):
    """Làm sạch triệt để khoảng trắng, dòng trống thừa và ký tự đặc biệt."""
    text = re.sub(r'[\r\n\t]+', '\n', text)
    lines = [line.strip() for line in text.split('\n')]
    non_empty_lines = [line for line in lines if line]
    cleaned_text = '\n'.join(non_empty_lines)
    cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
    return cleaned_text


def split_text_into_pages(full_text, chars_per_page=1500, smart_break=True):
    """Hàm dùng chung để chia văn bản thành các trang nhỏ."""
    pages = []
    length = len(full_text)
    start = 0

    while start < length:
        end = start + chars_per_page
        if end >= length:
            pages.append(full_text[start:].strip())
            break

        if smart_break:
            actual_end = full_text.rfind(' ', start, end)
            if actual_end == -1 or actual_end <= start:
                actual_end = end
        else:
            actual_end = end

        pages.append(full_text[start:actual_end].strip())
        start = actual_end

    return pages


# --- 2. CÁC HÀM XỬ LÝ TỪNG LOẠI FILE ---

def parse_epub_to_pages(uploaded_file, chars_per_page=1500, smart_break=True):
    book = epub.read_epub(uploaded_file)
    full_text_list = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            for element in soup(['script', 'style', 'head', 'meta']):
                element.decompose()
            raw_text = soup.get_text()
            cleaned_chapter = clean_text_advanced(raw_text)
            if cleaned_chapter:
                full_text_list.append(cleaned_chapter)

    full_text = '\n\n'.join(full_text_list)
    return split_text_into_pages(full_text, chars_per_page, smart_break)


def parse_pdf_to_pages(uploaded_file, chars_per_page=1500, smart_break=True):
    reader = PdfReader(uploaded_file)
    full_text = ""
    has_text = False

    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            full_text += text + "\n"
            has_text = True

    if not has_text:
        raise ValueError("File PDF này là dạng hình ảnh (Scanned PDF), ứng dụng chỉ hỗ trợ PDF thuần text!")

    cleaned_text = clean_text_advanced(full_text)
    return split_text_into_pages(cleaned_text, chars_per_page, smart_break)


def parse_txt_to_pages(uploaded_file, chars_per_page=1500, smart_break=True):
    raw_text = uploaded_file.read().decode('utf-8', errors='ignore')
    cleaned_text = clean_text_advanced(raw_text)
    return split_text_into_pages(cleaned_text, chars_per_page, smart_break)


def parse_docx_to_pages(uploaded_file, chars_per_page=1500, smart_break=True):
    doc = Document(uploaded_file)
    full_text_list = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    raw_text = '\n'.join(full_text_list)
    cleaned_text = clean_text_advanced(raw_text)
    return split_text_into_pages(cleaned_text, chars_per_page, smart_break)