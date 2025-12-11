# Vietnam Heritage AI API

REST API cho hệ thống trợ lý AI chuyên về văn hóa, lịch sử và văn học Việt Nam.

## Tính năng

- Trích xuất từ khóa thông minh từ câu hỏi
- Viết lại câu hỏi để tối ưu hóa tìm kiếm
- Tìm kiếm ngữ cảnh từ dataset Hugging Face
- Xếp hạng lại kết quả bằng Cross-Encoder
- Trả lời câu hỏi bằng LLM

## Cài đặt cục bộ

### Yêu cầu
- Python 3.9+
- pip

### Bước 1: Clone repository
```bash
git clone https://github.com/YOUR_USERNAME/vietnam-heritage-api.git
cd vietnam-heritage-api
```

### Bước 2: Tạo virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
```

### Bước 3: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình biến môi trường
```bash
cp .env.example .env
# Mở .env và thêm GROQ_API_KEY của bạn
```

### Bước 5: Chạy server
```bash
python app.py
```

Server sẽ chạy tại `http://localhost:5000`

## API Endpoints

### 1. Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

### 2. Hỏi đáp (Ask)
```
POST /ask
Content-Type: application/json

{
  "question": "Nguyễn Trãi sinh năm bao nhiêu?"
}
```

Response:
```json
{
  "question": "Nguyễn Trãi sinh năm bao nhiêu?",
  "answer": "Nguyễn Trãi sinh năm 1525..."
}
```

### 3. Home
```
GET /
```

Response:
```json
{
  "message": "Vietnam Heritage AI API",
  "endpoints": {...}
}
```

## Deploy trên Render.com

### Bước 1: Tạo GitHub Repository
1. Đăng nhập vào GitHub
2. Tạo repository mới: `vietnam-heritage-api`
3. Push code lên:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/vietnam-heritage-api.git
git push -u origin main
```

### Bước 2: Tạo tài khoản Render.com
1. Truy cập https://render.com
2. Đăng ký tài khoản bằng GitHub

### Bước 3: Deploy
1. Trong Render.com, click "New +" → "Web Service"
2. Kết nối GitHub repository `vietnam-heritage-api`
3. Cấu hình:
   - **Name**: `vietnam-heritage-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 2 --timeout 60`
   
4. Thêm Environment Variables:
   - **GROQ_API_KEY**: (Nhập API key của bạn)

5. Click "Create Web Service"

### Bước 4: Kiểm tra
Sau vài phút, ứng dụng sẽ được deploy. URL sẽ có dạng:
```
https://vietnam-heritage-api-xxxx.onrender.com
```

Kiểm tra:
```bash
curl https://vietnam-heritage-api-xxxx.onrender.com/health
```

## Sử dụng API

### Ví dụ với curl
```bash
curl -X POST https://vietnam-heritage-api-xxxx.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Nguyễn Trãi là ai?"}'
```

### Ví dụ với Python
```python
import requests

url = "https://vietnam-heritage-api-xxxx.onrender.com/ask"
data = {"question": "Nguyễn Trãi là ai?"}

response = requests.post(url, json=data)
print(response.json())
```

### Ví dụ với JavaScript
```javascript
fetch("https://vietnam-heritage-api-xxxx.onrender.com/ask", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    question: "Nguyễn Trãi là ai?"
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Khắc phục sự cố

### API key không được thiết lập
- Đảm bảo biến `GROQ_API_KEY` được thêm vào Environment Variables trên Render.com

### Lỗi "Module not found"
- Chạy `pip install -r requirements.txt`

### Server timeout
- Tăng `--timeout` giá trị trong start command

## Giới hạn

- **Render.com Plan**: Sử dụng **Standard Plan** hoặc cao hơn (Free Plan không đủ RAM/CPU)
- **Thời gian khởi động**: ~30-60 giây (lần đầu load dataset và models)
- **Thời gian xử lý**: 120 giây trên một request
- **RAM yêu cầu**: ≥ 1GB (FAISS + embedding models cần nhiều RAM)
- **CPU**: Tối thiểu 0.5 vCPU

## Khắc Phục Sự Cố

### Build Error: "Cannot import 'setuptools.build_meta'"
**Nguyên nhân**: Phiên bản pip trên Render cũ
**Giải pháp**: Đã thêm `pip install --upgrade pip setuptools wheel` vào build command trong `render.yaml`


## Cấu trúc project

```
.
├── app.py                # Flask REST API
├── main.py               # Logic chính
├── requirements.txt      # Dependencies
├── render.yaml           # Cấu hình Render.com
├── .env.example          # Mẫu biến môi trường
├── .gitignore           # Git ignore rules
└── README.md            # Tài liệu này
```

## License

MIT
