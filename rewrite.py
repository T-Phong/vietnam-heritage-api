from groq import Groq
from reranking import advanced_search
import os
from dotenv import load_dotenv

load_dotenv()

#groq_api_key = os.environ.get("GROQ_API_KEY")
groq_api_key = os.getenv('GROQ_API_KEY')

if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

client = Groq(api_key=groq_api_key)

class QueryRewriter:
    def __init__(self, model_name="Qwen/Qwen2.5-3B-Instruct"):
        print(f"⏳ Đang tải LLM {model_name} (khoảng 1-2 phút)...")
        # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # # Cấu hình 4-bit
        # bnb_config = BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_compute_dtype=torch.float16,
        #     bnb_4bit_use_double_quant=True,
        # )
        # # Load model ở chế độ float16 để tiết kiệm VRAM và chạy nhanh trên T4 GPU
        # self.model = AutoModelForCausalLM.from_pretrained(
        #     model_name,
        #     torch_dtype=torch.float16,
        #     device_map="auto"
        # )
        print("✅ Đã tải xong LLM.")

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

        # model pull
        # messages = [
        #     {"role": "system", "content": KEYWORD_EXTRACTOR_PROMPT},
        #     {"role": "user", "content": user_content}
        # ]
        
        # text = self.tokenizer.apply_chat_template(
        #     messages, tokenize=False, add_generation_prompt=True
        # )
        
        # model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # with torch.no_grad():
        #     generated_ids = self.model.generate(
        #         **model_inputs,
        #         max_new_tokens=40,
        #         temperature=0.1, # Giữ creativity thấp để kết quả ổn định
        #         do_sample=True
        #     )
            
        # generated_ids = [
        #     output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        # ]
        
        # response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        # keywords = [k.strip() for k in response.split(',') if k.strip()]
    
        # model call api
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages = [
                    {"role": "system", "content": KEYWORD_EXTRACTOR_PROMPT},
                    {"role": "user", "content": user_content}
                ]
        )
        #print(completion.choices[0].message.content)
        keywords = [k.strip() for k in completion.choices[0].message.content.split(',') if k.strip()]
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
          5. LƯU Ý: NẾU ĐÂY CHỈ LÀ 1 CÂU GIAO TIẾP BÌNH THƯỜNG NHƯ CHÀO HỎI, HÃY TRẢ VỀ NGUYÊN VĂN NHƯ VẬY.

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

        #model pull
        # messages = [
        #     {"role": "system", "content": CONCISE_REWRITE_PROMPT},
        #     {"role": "user", "content": user_content}
        # ]
        
        # text = self.tokenizer.apply_chat_template(
        #     messages, tokenize=False, add_generation_prompt=True
        # )
        
        # model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # with torch.no_grad():
        #     generated_ids = self.model.generate(
        #         **model_inputs,
        #         max_new_tokens=64,
        #         temperature=0.1, # Giữ creativity thấp để kết quả ổn định
        #         do_sample=False
        #     )
            
        # generated_ids = [
        #     output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        # ]
        
        # response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        #model api
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages = [
                    {"role": "system", "content": CONCISE_REWRITE_PROMPT},
                    {"role": "user", "content": user_content}
                ]
        )
        #print(completion.choices[0].message.content)
        return completion.choices[0].message.content.strip()
    
    def ask_with_context(self,question,history):
        
        # get key word
        keyword = self.keyword(question,history)
        print(f"\n--- keyword: {keyword} ---")
        
        # rewrite question with key word
        q_rewrite = self.rewrite(question,keyword)
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
            4. NẾU KHÔNG CÓ DỮ LIỆU NGỮ CẢNH VÀ CÂU HỎI NGƯỜI DÙNG CHỈ LÀ NHỮNG CÂU GIAO TIẾP BÌNH THƯỜNG (NHƯ CHÀO HỎI), HÃY TRẢ LỜI NGƯỜI DÙNG VỚI TƯ CÁCH LÀ MỘT TRỢ LÝ LỊCH SỰ VÀ THÂN THIỆN.
            
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

        # pull model
        # messages = [
        #         {"role": "system", "content": RAG_SYSTEM_PROMPT},
        #         {"role": "user", "content": user_content}
        #     ]

        # # Format prompt theo chuẩn của Qwen
        # text = tokenizer.apply_chat_template(
        #     messages,
        #     tokenize=False,
        #     add_generation_prompt=True
        # )

        # # Đưa input vào đúng device của model_base
        # model_inputs = tokenizer([text], return_tensors="pt").to(model_base.device)

        # # --- SỬA LỖI TẠI ĐÂY ---
        # # Dùng model_base (Qwen) thay vì model (SentenceTransformer)
        # generated_ids = model_base.generate(
        #     **model_inputs,  # Lưu ý: sửa cả tên biến input cho khớp (model_inputs thay vì model_base1 cho rõ nghĩa)
        #     max_new_tokens=512,
        #     temperature=0.1, 
        #     top_p=0.9
        # )

        # generated_ids = [
        #     output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        # ]

        # response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages = [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        return completion.choices[0].message.content.strip()