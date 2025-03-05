import streamlit as st
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import io
from docx import Document
import os
import shutil

# Đảm bảo Tesseract được cài đặt và cấu hình đúng trên hệ thống
# Ví dụ: cài gói tiếng Việt nếu cần: `tesseract-ocr-vie`

# Hàm trích xuất văn bản từ PDF
def extract_text_from_pdf(pdf_path):
    """
    Trích xuất văn bản từ file PDF. Nếu văn bản không thể trích xuất trực tiếp,
    chuyển đổi PDF thành hình ảnh và sử dụng OCR.
    
    Args:
        pdf_path (str): Đường dẫn đến file PDF.
    Returns:
        str: Văn bản trích xuất từ file PDF.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Thử trích xuất văn bản trực tiếp
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    # Nếu không có văn bản, chuyển đổi trang thành hình ảnh và dùng OCR
                    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
                    for image in images:
                        text += pytesseract.image_to_string(image, lang='eng+vie') + "\n"
    except Exception as e:
        st.error(f"Lỗi khi xử lý PDF: {e}")
        return None
    return text

# Hàm trích xuất văn bản từ hình ảnh
def extract_text_from_image(image_path):
    """
    Trích xuất văn bản từ file hình ảnh bằng OCR.
    
    Args:
        image_path (str): Đường dẫn đến file hình ảnh.
    Returns:
        str: Văn bản trích xuất từ hình ảnh.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='eng+vie')
        return text
    except Exception as e:
        st.error(f"Lỗi khi xử lý hình ảnh: {e}")
        return None

# Hàm tạo file Word từ văn bản
def create_word_file(text, output_path):
    """
    Tạo file Word từ văn bản trích xuất.
    
    Args:
        text (str): Văn bản cần ghi vào file Word.
        output_path (str): Đường dẫn đến file Word đầu ra.
    Returns:
        bool: True nếu tạo file thành công, False nếu thất bại.
    """
    try:
        doc = Document()
        doc.add_paragraph(text)
        doc.save(output_path)
        return True
    except Exception as e:
        st.error(f"Lỗi khi tạo file Word: {e}")
        return False

# Hàm chính để chạy ứng dụng
def main():
    """Xây dựng giao diện Streamlit và xử lý logic chính của ứng dụng."""
    st.title("Trích Xuất Văn Bản Từ CV")
    st.write("Tải lên CV (PDF hoặc hình ảnh) để trích xuất văn bản và nhận file Word.")

    # Tạo thư mục tạm nếu chưa tồn tại
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Widget tải file
    uploaded_file = st.file_uploader(
        "Chọn file CV", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        # Lưu file tạm thời
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Xác định loại file và trích xuất văn bản
        file_type = uploaded_file.type
        if file_type == "application/pdf":
            st.write("Đang xử lý file PDF...")
            text = extract_text_from_pdf(temp_file_path)
        else:
            st.write("Đang xử lý file hình ảnh...")
            text = extract_text_from_image(temp_file_path)

        # Kiểm tra kết quả trích xuất
        if text:
            st.success("Trích xuất văn bản thành công!")
            st.text_area("Văn bản trích xuất", text, height=200)

            # Tạo file Word
            output_path = os.path.join(temp_dir, "cv_output.docx")
            if create_word_file(text, output_path):
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="Tải xuống file Word",
                        data=file,
                        file_name="cv_text.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        else:
            st.error("Không thể trích xuất văn bản từ file.")

        # Dọn dẹp file tạm thời
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(output_path):
            os.remove(output_path)

    # Hiển thị hướng dẫn
    st.sidebar.header("Hướng dẫn")
    st.sidebar.write("""
    1. Tải lên file CV (PDF hoặc hình ảnh).
    2. Chờ xử lý và xem văn bản trích xuất.
    3. Tải xuống file Word chứa văn bản.
    """)

if __name__ == "__main__":
    try:
        main()
    finally:
        # Dọn dẹp thư mục tạm khi ứng dụng kết thúc (tùy chọn)
        if os.path.exists("temp"):
            shutil.rmtree("temp")