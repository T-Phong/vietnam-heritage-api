### Block 2: Import thư viện
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import torch
from datasets import load_dataset
from groq import Groq
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment variable
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=groq_api_key)

# Global variables for lazy loading
_dataset = None
_vectors = None
_metadata = None
_ids = None
_index = None
_model = None
_reranker = None

def load_dataset_and_index():
    """Lazy load dataset and FAISS index"""
    global _dataset, _vectors, _metadata, _ids, _index
    
    if _index is not None:
        logger.info("Dataset and FAISS index already loaded, skipping...")
        return
    
    logger.info("Loading dataset from Hugging Face...")
    _dataset = load_dataset("synguyen1106/vietnam_heritage_embeddings_v2", split="train")
    
    logger.info("Processing vectors...")
    _vectors = np.array(_dataset['embedding']).astype("float32")
    
    logger.info("Extracting metadata...")
    _metadata = [
        {k:v for k,v in _dataset[i].items() if k not in ['embedding','id','slug']}
        for i in range(len(_dataset))
    ]
    _ids = [_dataset[i]['id'] for i in range(len(_dataset))]
    
    logger.info(f"Loaded {len(_ids)} items from dataset.")
    
    logger.info("Creating FAISS index...")
    d = _vectors.shape[1]
    _index = faiss.IndexFlatL2(d)
    _index.add(_vectors)
    logger.info(f"FAISS index created with {_index.ntotal} vectors")

def get_model():
    """Lazy load embedding model"""
    global _model
    if _model is None:
        logger.info("Loading embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_reranker():
    """Lazy load reranker model"""
    global _reranker
    if _reranker is None:
        logger.info("Loading reranker model...")
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _reranker
### Block 6: RAG query function
def retrieve_context(query, k=2):
    # Ensure dataset and models are loaded
    load_dataset_and_index()
    model = get_model()
    
    # Encode query
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search FAISS
    distances, indices = _index.search(query_vec, k)

    results = []
    for i, idx in enumerate(indices[0]):
        idx = int(idx)  # ép sang int để dataset HF nhận
        result = {
            "metadata": _metadata[idx]
        }
        results.append(result)
    return results

class QueryRewriter:
    def keyword(self, long_query,his):
        """Dùng LLM để tóm tắt query dài thành keyword tìm kiếm"""

        conversation_str = ""
        for turn in his:
            conversation_str += f"{turn['role'].capitalize()}: {turn['content']}\n"
        KEYWORD_EXTRACTOR_PROMPT = """
          Bạn là một API trích xuất từ khóa thông minh (Context-Aware Keyword Extractor).
          Nhiệm vụ: Trích xuất danh sách các thực thể (Entity) và từ khóa quan trọng từ câu hỏi của người dùng để phục vụ tìm kiếm Database.

          QUY TRÌNH XỬ LÝ (BẮT BUỘC):
          1. Đọc "Lịch sử hội thoại" để hiểu ngữ cảnh.
          2. Nếu câu hỏi hiện tại dùng đại từ thay thế (nó, hắn, họ, cái đó, việc này...), hãy thay thế ngay lập tức bằng danh từ cụ thể đã nhắc đến trong lịch sử.
          3. Chỉ trích xuất: THỰC THỂ ĐỊNH DANH (Tên người, Biệt danh, Địa danh, Tổ chức, Sự kiện riêng) xuất hiện trong câu hỏi.
          4. Loại bỏ các từ vô nghĩa (tại sao, là gì, bao nhiêu, như thế nào).

          ĐỊNH DẠNG OUTPUT:
          - Chỉ trả về một dòng duy nhất chứa các từ khóa ngăn cách bằng dấu phẩy.
          - TUYỆT ĐỐI KHÔNG trả lời câu hỏi.
          - TUYỆT ĐỐI KHÔNG giải thích.

          ### VÍ DỤ MẪU (HỌC THEO CÁCH NÀY):

          Ví dụ 1:
          Lịch sử:
          User: "Giới thiệu về Vịnh Hạ Long."
          Assistant: "Vịnh Hạ Long là di sản thiên nhiên thế giới tại Quảng Ninh..."
          Input: "Ở đó có những hang động nào đẹp?"
          Output: Vịnh Hạ Long, hang động
          (Giải thích: "Ở đó" được hiểu là "Vịnh Hạ Long").

          Ví dụ 2:
          Lịch sử:
          User: "Shark Bình sinh năm bao nhiêu?"
          Assistant: "Shark Bình sinh năm 1981."
          Input: "Vợ của ông ấy tên là gì?"
          Output: Shark Bình, Vợ
          (Giải thích: "Ông ấy" được thay bằng "Shark Bình").

          Ví dụ 3:
          Lịch sử: (Rỗng)
          Input: "Cách làm món sườn xào chua ngọt."
          Output: sườn xào chua ngọt

          HÃY BẮT ĐẦU:
          """
        user_content = f"""
          ### Lịch sử hội thoại:
          {conversation_str}

          ### Câu hỏi hiện tại (Input):
          "{long_query}"

          ### Output (Danh sách từ khóa):"""

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages = [
                {"role": "system", "content": KEYWORD_EXTRACTOR_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        response = completion.choices[0].message.content.strip()
        
        keywords = [k.strip() for k in response.split(',') if k.strip()]
    
        # --- QUAN TRỌNG: HARD LIMIT ---
        return keywords[:3]

    def rewrite(self, long_query,keywords):
        """Dùng LLM để tóm tắt query dài thành keyword tìm kiếm"""
        CONCISE_REWRITE_PROMPT = """
          Bạn là chuyên gia biên tập câu hỏi tìm kiếm (Search Query Editor).

          NHIỆM VỤ:
          Viết lại câu hỏi của người dùng dựa trên "Câu hỏi gốc" và "Từ khóa gợi ý" sao cho:
          1. ĐẦY ĐỦ Ý: Nếu câu hỏi thiếu chủ ngữ hoặc dùng đại từ (nó, cái này...), hãy chèn từ khóa vào để làm rõ.
          2. NGẮN GỌN: Loại bỏ hoàn toàn các từ ngữ xã giao thừa thãi (ví dụ: "dạ cho em hỏi", "làm ơn", "với ạ", "mình muốn biết là"...).
          3. TRỰC DIỆN: Biến nó thành một câu truy vấn thông tin chuẩn xác.
          4. CHỈ TRẢ VỀ TIẾNG VIỆT CÓ DẤU!

          QUY TẮC:
          - Giữ nguyên ý định của người dùng.
          - TUYỆT ĐỐI KHÔNG trả lời câu hỏi.
          - Chỉ trả về 1 dòng kết quả là câu trả lời đã được viết lại.

          VÍ DỤ MẪU:
          ---
          Input: "Dạ anh ơi cho em hỏi xíu là cái con này nó pin trâu không ạ?"
          Keywords: [Samsung S23 Ultra, pin]
          Output: Pin Samsung S23 Ultra có tốt không?
          (Giải thích: Loại bỏ "Dạ anh ơi...", thay "con này" bằng "Samsung S23 Ultra").

          Input: "Cách nấu món bò kho sao cho ngon nhất vậy shop?"
          Keywords: [Bò kho, cách nấu]
          Output: Cách nấu Bò kho ngon nhất.
          (Giải thích: Câu hỏi đã có đầy đủ thông tin chủ ngữ và vị ngữ nên chỉ cần tóm tắt lại mà không cần dựa vào keywords)

          Input: "Năm sinh?"
          Keywords: ['Nguyễn Trãi']
          Output: Nguyễn trãi sinh năm bao nhiêu?
          ---

          HÃY BẮT ĐẦU:
          """
        
        keywords_str = ", ".join(keywords) if keywords else "Không có"

        user_content = f"""
          Câu hỏi gốc: "{long_query}"
          Keywords: [{keywords_str}]

          Output:"""

        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages = [
                {"role": "system", "content": CONCISE_REWRITE_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        response = completion.choices[0].message.content.strip()

        return response.strip()

def format_metadata_list_to_context(metadata_list):
    """
    Chuyển đổi danh sách metadata (List[Dict]) thành văn bản ngữ cảnh (String).
    """
    # Kiểm tra an toàn: Nếu input không phải list, bọc nó lại thành list
    if isinstance(metadata_list, dict):
        metadata_list = [metadata_list]
    
    if not metadata_list:
        return "Không có dữ liệu ngữ cảnh."
    
    full_context_text = ""
    metadata_list_result = []
    for m in metadata_list:
        metadata_list_result.append(m['metadata'])
    # Lặp qua từng hồ sơ trong danh sách
    for index, data in enumerate(metadata_list_result, 1):
        # 1. Trích xuất dữ liệu (Dùng .get để tránh lỗi nếu thiếu trường)
        ten = data.get('ten', 'Không rõ tên')
        mo_ta = data.get('mo_ta', '')
        
        # Nhóm thông tin phân loại
        loai_hinh = data.get('loai_hinh', 'N/A')
        chu_de = data.get('chu_de', 'N/A')
        dan_toc = data.get('dan_toc', 'N/A')
        
        # Nhóm thời gian & không gian
        nien_dai = data.get('nien_dai', 'N/A')
        thoi_ky = data.get('thoi_ky', 'N/A')
        vung_mien = data.get('vung_mien', 'N/A')
        dia_diem = data.get('dia_diem', 'N/A')
        
        # Nhóm giá trị nội dung
        y_nghia = data.get('y_nghia', '')
        tac_pham = data.get('nguyen_lieu_chinh', '') # Với Nguyễn Trãi là tác phẩm
        nhan_vat = data.get('nhan_vat_lien_quan', '')

        # 2. Tạo template văn bản cho TỪNG hồ sơ
        # Dùng dấu phân cách rõ ràng để Model không lẫn lộn giữa Sọ Dừa và Nguyễn Trãi
        profile_text = f"""
        ==================================================
        HỒ SƠ SỐ {index}: {ten.upper()}
        ==================================================
        
        [TỔNG QUAN]
        {mo_ta}
        
        [THÔNG TIN CHI TIẾT]
        - Phân loại: {loai_hinh} (Chủ đề: {chu_de})
        - Dân tộc: {dan_toc}
        - Thời gian: {nien_dai} ({thoi_ky})
        - Địa danh/Vùng miền: {vung_mien} - {dia_diem}
        
        [GIÁ TRỊ & LIÊN QUAN]
        - Tác phẩm/Di sản chính: {tac_pham}
        - Ý nghĩa: {y_nghia}
        - Nhân vật liên quan: {nhan_vat}
        """
        
        # 3. Ghép vào chuỗi tổng
        full_context_text += profile_text + "\n"

    return full_context_text

def advanced_search(query, keyword):
    load_dataset_and_index()
    reranker = get_reranker()
    
    result = []
    for r in keyword:
        result +=retrieve_context(r, k=10)
    # 1. Bước làm sạch (Query Rewriting)
    short_query = query
    pairs_to_score = []
    # 3. Bước lọc tinh (Reranking)
    # Tạo cặp (Câu hỏi, Đoạn văn) để chấm điểm
    for item in result:
            # --- KỸ THUẬT QUAN TRỌNG: TEXT CONSTRUCTION ---
            # Ghép các trường JSON lại thành một đoạn văn có nghĩa để model hiểu
            # Nếu chỉ đưa 'content' thì model sẽ thiếu ngữ cảnh (không biết dân tộc nào)
            constructed_text = (
                f"tên: {item['metadata'].get('ten', '')}. "
                f"mô tả: {item['metadata'].get('mo_ta', '') }. "
            )
            #print("constructed_text",constructed_text)
            #print("\n")
            # --- KỸ THUẬT QUAN TRỌNG: TEXT CONSTRUCTION ---
            pairs_to_score.append([query, constructed_text])
            
    scores = reranker.predict(pairs_to_score)
    #print("scores",scores,item['metadata'].get('ten', ''))
    # Gán điểm và sắp xếp lại
    for i, doc in enumerate(result):
        doc['rerank_score'] = scores[i]
        
    # Sắp xếp giảm dần theo điểm Rerank
    sorted_docs = sorted(result, key=lambda x: x['rerank_score'], reverse=True)
    
    # Lấy Top K tốt nhất
    return format_metadata_list_to_context(sorted_docs[:3])

rewriter = QueryRewriter()
history = []




def ask_with_context(question):
    global history
    
    # get key word
    keyword = rewriter.keyword(question,history)
    print(f"\n--- keyword: {keyword} ---")
    
    # rewrite question with key word
    q_rewrite = rewriter.rewrite(question,keyword)
    print(f"\n--- q_rewrite: {q_rewrite} ---")
    # get top 30 RAG and reranking by question rewrite and keyword then get 5
    p = advanced_search(q_rewrite,keyword)
    RAG_SYSTEM_PROMPT = """
        Bạn là Trợ lý AI Thông minh chuyên về Văn hóa, Lịch sử và Văn học Việt Nam.
        Nhiệm vụ: Trả lời câu hỏi người dùng dựa trên "DANH SÁCH HỒ SƠ" được cung cấp trong Context.
        
        HƯỚNG DẪN XỬ LÝ:
        1. Xác định đối tượng: Đọc câu hỏi để biết người dùng đang hỏi về hồ sơ nào (Ví dụ: hỏi về "Nguyễn Trãi" hay "Sọ Dừa").
        2. Tra cứu thông tin:
           - Nếu hỏi về thời gian/địa điểm: Tìm trong mục [THÔNG TIN CHI TIẾT].
           - Nếu hỏi về bài học/giá trị: Tìm trong mục [GIÁ TRỊ & LIÊN QUAN] hoặc [TỔNG QUAN].
        3. Tổng hợp: Nếu câu hỏi yêu cầu liệt kê (VD: "Có những nhân vật nào trong tài liệu?"), hãy đọc tên của tất cả hồ sơ.
        
        QUY TẮC TRẢ LỜI:
        - Trả lời ngắn gọn, đúng trọng tâm.
        - Nếu thông tin không có trong bất kỳ hồ sơ nào, hãy trả lời: "Xin lỗi, tài liệu được cung cấp không chứa thông tin này."
        - KHÔNG dùng kiến thức bên ngoài nếu không có trong hồ sơ.
        """
    
    # Tạo nội dung user prompt: Ghép context và câu hỏi gốc
    user_content = f"""### Context:
{p}

### User Question:
{q_rewrite}
"""

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages = [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
    )
    response = completion.choices[0].message.content.strip()
    
    history.append({"role": "user", "content": question}) 
    history.append({"role": "assistant", "content": response})
    if len(history) > 5:
        history = history[-5:]
    return response

# --- VÍ DỤ THỰC TẾ ---
