# Hướng Dẫn Deploy Chi Tiết

## 🔍 Tổng Quan Vấn Đề Đã Giải Quyết

Phiên bản này đã **tối ưu hóa** để xử lý các vấn đề deployment:

### ❌ Vấn Đề Cũ:
- Khi import `main.py`, toàn bộ FAISS index + embedding models được load ngay lập tức
- Điều này mất **5-10 phút** chỉ để khởi động
- Render.com free plan sẽ timeout và deploy thất bại

### ✅ Giải Pháp Mới:
- **Lazy Loading**: Models chỉ load khi request đầu tiên tới
- **Singleton Pattern**: Mỗi model chỉ load 1 lần, sau đó được cache
- **Logging**: Theo dõi quá trình khởi động
- **FAISS Index**: Load cùng với embeddings (bước đầu)

---

## 📦 Kiến Trúc Ứng Dụng

```
main.py
├── [Block 2] Import + Config API key
├── [Global Variables] Lưu trữ cached models (_dataset, _index, etc.)
├── [Lazy Loading Functions]
│   ├── load_dataset_and_index() → Lần đầu tiên được gọi
│   ├── get_model() → Load embedding model
│   └── get_reranker() → Load CrossEncoder model
├── [RAG Pipeline Functions]
│   ├── retrieve_context() → Gọi load_dataset_and_index()
│   ├── advanced_search() → Gọi get_reranker()
│   └── ask_with_context() → Main function (được gọi từ API)
└── [Helper Classes]
    └── QueryRewriter → Keyword extraction + Query rewriting

app.py
├── Flask app initialization
├── before_request() → Gọi load_dataset_and_index() lần đầu
├── POST /ask → Main endpoint
├── GET /health → Health check
└── GET / → Documentation
```

---

## 🚀 Bước Deploy Chi Tiết

### **Bước 1: Chuẩn Bị GitHub**

#### Tạo Repository Mới:
```powershell
# Mở https://github.com/new
# Điền thông tin:
# - Repository name: vietnam-heritage-api
# - Description: Vietnam Heritage AI REST API with RAG
# - Public (để Render.com có thể access)
# - Click "Create repository"
```

#### Push code:
```powershell
cd "c:\Users\Thanh Phong\Desktop\Study\HK3\chuyende\api"

# Xem git status
git status

# Setup remote (thay YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/vietnam-heritage-api.git
git branch -M main
git push -u origin main
```

### **Bước 2: Tạo Tài Khoản Render.com**

1. Truy cập https://render.com
2. Click "Sign up"
3. Đăng nhập bằng **GitHub account**
4. Authorize Render để access GitHub repositories

### **Bước 3: Deploy Service**

**Quan trọng**: Chọn **Standard Plan** hoặc cao hơn (Free Plan sẽ timeout)

1. Trong Render Dashboard, click **"New +"** → **"Web Service"**
2. Kết nối repository:
   - Chọn `vietnam-heritage-api`
   - Click "Connect"
3. Cấu hình Service:
   - **Name**: `vietnam-heritage-api` (hoặc tên khác)
   - **Environment**: `Python 3`
   - **Region**: Chọn gần với bạn nhất (Singapore, Tokyo, hoặc US-Oregon)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --worker-class sync --timeout 120 --max-requests 10`
   - **Plan**: Chọn **Standard** (≥ $7/month) hoặc **Premium** (≥ $25/month)

4. Thêm Environment Variables:
   - Click **"Add Environment Variable"**
   - **Name**: `GROQ_API_KEY`
   - **Value**: (Nhập API key từ groq.com)
   - Click **"Add"**

5. Click **"Create Web Service"**

### **Bước 4: Monitoring Deployment**

1. Trong Render Dashboard, xem logs:
   ```
   Initializing app: Loading dataset and models...
   Loading dataset from Hugging Face...
   Processing vectors...
   Extracting metadata...
   Loaded 48 items from dataset.
   Creating FAISS index...
   FAISS index created with 48 vectors
   Loading embedding model...
   App initialization complete!
   ```

2. Sau khi thấy "App initialization complete!", service đã ready

### **Bước 5: Test API**

```bash
# Health check
curl https://YOUR_SERVICE_URL.onrender.com/health

# Test hỏi đáp
curl -X POST https://YOUR_SERVICE_URL.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Nguyễn Trãi là ai?"}'
```

---

## 📊 Khắc Phục Sự Cố

### ❌ Lỗi: "Build failed" hoặc "Timeout"
**Nguyên nhân**: Free Plan không đủ resources
**Giải pháp**: Nâng cấp lên **Standard Plan**

### ❌ Lỗi: "GROQ_API_KEY not set"
**Nguyên nhân**: Environment variable không được thêm
**Giải pháp**: 
1. Vào Render Dashboard → Service settings
2. Thêm `GROQ_API_KEY` environment variable

### ❌ API responds slowly (>120s)
**Nguyên nhân**: Lần đầu request cần load models (~60s)
**Giải pháp**: 
- Request thứ 2 trở đi sẽ nhanh hơn (models đã cached)
- Upgrade CPU plan nếu cần tốc độ cao hơn

### ❌ "502 Bad Gateway"
**Nguyên nhân**: Service quá tải hoặc crashed
**Giải pháp**:
1. Kiểm tra logs trong Render Dashboard
2. Restart service
3. Upgrade resources nếu cần

---

## 💾 File Structure

```
vietnam-heritage-api/
├── app.py                  # Flask REST API
├── main.py                 # Core RAG logic (lazy loading)
├── requirements.txt        # Python dependencies
├── render.yaml            # Render.com config
├── .env.example           # Mẫu environment variables
├── .gitignore             # Git ignore rules
├── README.md              # Tài liệu cơ bản
└── DEPLOYMENT.md          # File này
```

---

## 🔐 Security Best Practices

1. **KHÔNG** hardcode API keys trong code
2. **LUÔN** sử dụng environment variables
3. Giữ `.env` file trong `.gitignore`
4. Xem xét sử dụng API keys rotation

---

## 📈 Performance Metrics

| Giai đoạn | Thời gian | Ghi chú |
|-----------|----------|--------|
| Khởi động lần đầu | 30-60s | Load dataset + models |
| Khởi động lần 2+ | <1s | Models cached |
| Request lần đầu | 20-30s | Inference + API call |
| Request lần 2+ | 15-20s | Faster (cached embeddings) |

---

## 🔄 Tự Động Deploy

Khi bạn push code lên GitHub:
```bash
git push -u origin main
```

Render.com sẽ **tự động**:
1. Detect changes trên GitHub
2. Pull latest code
3. Build lại ứng dụng
4. Deploy service mới (không downtime)

---

## 📞 Support & Resources

- **Groq API**: https://console.groq.com/
- **Render.com Docs**: https://render.com/docs
- **Hugging Face Datasets**: https://huggingface.co/datasets
- **FAISS Docs**: https://github.com/facebookresearch/faiss

