# 1. Dùng Python 3.10 (tương thích tốt với Faiss/Torch mới)
FROM python:3.10-slim

# 2. Thiết lập thư mục làm việc
WORKDIR /app

# 3. Copy file requirements trước (để tận dụng cache)
# Nếu bạn vẫn dùng tên 'requirements_rag.txt' thì sửa dòng dưới thành:
COPY requirements_rag.txt requirements.txt

# 4. Cài đặt thư viện
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy toàn bộ code vào container
COPY . .

# 6. Tạo user non-root (Bắt buộc đối với Hugging Face Spaces để tránh lỗi Permission)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 7. Mở port 7860 (Port mặc định của HF Spaces)
EXPOSE 7860

# 8. Lệnh chạy server
# "app:app" nghĩa là: trong file app.py, tìm object tên là app (biến Flask)
CMD ["/path/to/venv/bin/gunicorn", "-w", "4", "main:app"]

# Hoặc kích hoạt venv trước (ít dùng trong CMD):
CMD [ "/bin/bash", "-c", "source venv/bin/activate && gunicorn -w 4 main:app" ]