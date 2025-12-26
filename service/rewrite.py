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
          Output: Vịnh Hạ Long
          (Giải thích: "Ở đó" được hiểu là "Vịnh Hạ Long").

          Ví dụ 2:
          Lịch sử:
          User: "Các lễ hội nổi tiếng ở VN"
          Assistant: "Việt Nam có nhiều lễ hội nổi tiếng, trong đó có:
            - **Lễ hội Lim**: Là lễ hội lớn của tỉnh Bắc Ninh, được tổ chức vào ngày 13 tháng Giêng hằng năm trên địa bàn huyện Tiên Du. Đây là nét kết tinh độc đáo của vùng văn hoá Kinh Bắc, với trung tâm là các hoạt động ca hát Quan họ Bắc Ninh.
            - Ngoài ra, còn có nhiều lễ hội khác như lễ hội đua thuyền, lễ hội đền, chùa,... khắp cả nước.
            Nếu bạn muốn tìm hiểu thêm về các lễ hội khác, vui lòng cho tôi biết!"
          Input: "Ở đó có gì hay?"
          Output: "Lễ hội Lim, lễ hội đua thuyền, lễ hội đền"
          (Giải thích: "Ở đó" được hiểu là "Lễ hội Lim, lễ hội đua thuyền, lễ hội đền").

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

    def rewrite_query(self, long_query,history):
        """Dùng LLM để tóm tắt query dài thành keyword tìm kiếm"""
        conversation_str = ""
        for turn in history:
            conversation_str += f"{turn['role'].capitalize()}: {turn['content']}\n"

        CONCISE_REWRITE_PROMPT = """
          Bạn là chuyên gia biên tập câu hỏi tìm kiếm (Search Query Editor).

          NHIỆM VỤ:
          Viết lại câu hỏi của người dùng dựa trên "Câu hỏi gốc" và "Lịch sử hội thoại" sao cho:
          1. ĐẦY ĐỦ Ý: Nếu câu hỏi thiếu chủ ngữ hoặc dùng đại từ (nó, cái này...), hãy đọc lịch sử để bổ sung cho đầy đủ.
          2. NGẮN GỌN: Loại bỏ hoàn toàn các từ ngữ xã giao thừa thãi (ví dụ: "dạ cho em hỏi", "làm ơn", "với ạ", "mình muốn biết là"...).
          3. TRỰC DIỆN: Biến nó thành một câu truy vấn thông tin chuẩn xác.
          4. CHỈ TRẢ VỀ TIẾNG VIỆT CÓ DẤU!
          5. LƯU Ý: NẾU ĐÂY CHỈ LÀ 1 CÂU GIAO TIẾP BÌNH THƯỜNG NHƯ CHÀO HỎI, HÃY TRẢ VỀ NGUYÊN VĂN NHƯ VẬY.

          QUY TẮC:
          - Giữ nguyên ý định của người dùng.
          - Nếu câu hỏi có nội dung mang tính tìm hiểu thêm (ví dụ: còn gì khác, thêm, ngoài ra, v.v...), hãy giữ nguyên ý đó.
          - TUYỆT ĐỐI KHÔNG trả lời câu hỏi.
          - Chỉ trả về 1 dòng kết quả là câu hỏi đã được viết lại.

          VÍ DỤ MẪU:
          ---
          Lịch sử:
          User: "Giới thiệu về Vịnh Hạ Long."
          Assistant: "Vịnh Hạ Long là di sản thiên nhiên thế giới tại Quảng Ninh..."
          Input: "Thuộc tỉnh nào?"
          Output: Vịnh Hạ Long thuộc tỉnh nào?
          (Giải thích: "Thuộc tỉnh nào?" dùng đại từ thay thế, cần bổ sung thành câu đầy đủ).

          Lịch sử:
          User: "các địa điểm du lịch ở miền bắc"
          Assistant: "Các địa điểm du lịch ở miền Bắc mà bạn có thể tham khảo bao gồm:
                        1. **Hồ Ba Bể** (Bắc Kạn): Hồ nước ngọt tự nhiên lớn nhất Việt Nam, nằm trong Vườn quốc gia Ba Bể, nổi tiếng với cảnh quan sơn thủy hữu tình và hệ sinh thái đa dạng
                        2. **Đền Ngọc Sơn** (Hà Nội): Một ngôi đền tọa lạc trên đảo Ngọc, thuộc Hồ Hoàn Kiếm, Hà Nội, được xây dựng vào thế kỷ XIX, thờ Văn Xương Đế Quân, Quan Công và Trần Hưng Đạo.
                        3. **Hồ Hoàn Kiếm** (Hà Nội): Một biểu tượng văn hóa và lịch sử của thủ đô Hà Nội.
                        Những địa điểm này thể hiện sự đa dạng về văn hóa, lịch sử và cảnh quan thiên nhiên của miền Bắc Việt Nam."
          Input: "còn chỗ nào khác không?"
          Output: "Ngoài Hồ Ba Bể, Đền Ngọc Sơn và Hồ Hoàn Kiếm, miền Bắc còn có nhiều địa điểm du lịch khác?"
          (Giải thích: "Thuộc tỉnh nào?" dùng đại từ thay thế, cần bổ sung thành câu đầy đủ).
          ---

          HÃY BẮT ĐẦU:
          """
        

        user_content = f"""
          ### Lịch sử hội thoại:
          {conversation_str}

          ### Câu hỏi gốc (Input):
          "{long_query}"

          ### Output (Câu hỏi đã được viết lại):"""

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
    
    # Thêm vào class QueryRewriter trong rewrite.py
    def generate_hypothetical_answer(self, query):
        HYDE_PROMPT = f"""Bạn là một trợ lý AI am hiểu văn hóa Việt Nam. Hãy viết một đoạn văn trả lời chi tiết cho câu hỏi sau đây. Đoạn văn này chỉ dùng để làm tài liệu giả định cho việc tìm kiếm, không cần phải chính xác 100%.

        Câu hỏi: "{query}"

        Đoạn văn trả lời giả định:"""
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct", # Hoặc model bạn chọn
            messages=[{"role": "user", "content": HYDE_PROMPT}]
        )
        hypothetical_answer = completion.choices[0].message.content.strip()
        return hypothetical_answer


    def ask_with_context(self,question,history):
        
        # get key word
        keyword = self.keyword(question,history)
        print(f"\n--- keyword: {keyword} ---")
        print(type(keyword))
        # rewrite question with key word
        q_rewrite = self.rewrite_query(question,history)
        print(f"\n--- q_rewrite: {q_rewrite} ---")
        fake_answer = self.generate_hypothetical_answer(q_rewrite)
        print(f"\n--- fake_answer: {fake_answer} ---")
        # get top 30 RAG and reranking by question rewrite and keyword then get 5
        p = advanced_search(fake_answer,keyword) 
        print(f"\n--- context p: {p} ---")
        RAG_SYSTEM_PROMPT = """Bạn là một trợ lý AI chuyên trả lời các câu hỏi về văn hóa các dân tộc Việt Nam.
                NHIỆM VỤ CỐT LÕI: Trả lời câu hỏi của người dùng CHỈ DỰA VÀO thông tin được cung cấp trong phần "Dữ liệu Ngữ cảnh" dưới đây. TUYỆT ĐỐI không sử dụng bất kỳ kiến thức nào bạn đã được huấn luyện trước đó.

                HƯỚNG DẪN XỬ LÝ:
                1.  **Phân tích câu hỏi**: Đọc kỹ câu hỏi của người dùng để hiểu rõ họ đang muốn biết thông tin gì và về đối tượng nào (ví dụ: lễ hội, trang phục, phong tục...).
                2.  **Tra cứu trong ngữ cảnh**: Tìm kiếm thông tin chính xác trong "Dữ liệu Ngữ cảnh" để trả lời câu hỏi.
                    *   Nếu câu hỏi yêu cầu so sánh (ví dụ: "so sánh A và B"), hãy tìm thông tin về cả A và B trong ngữ cảnh và chỉ ra các điểm tương đồng và khác biệt.
                    *   Nếu câu hỏi yêu cầu liệt kê (ví dụ: "kể tên các lễ hội..."), hãy tổng hợp tất cả các đối tượng phù hợp có trong ngữ cảnh.
                3.  **Tổng hợp và trả lời**: Dựa trên thông tin tìm được, hãy soạn một câu trả lời ngắn gọn, chính xác và đi thẳng vào vấn đề.

                QUY TẮC BẮT BUỘC:
                -   **TRUNG THỰC VỚI NGỮ CẢNH**: Mọi thông tin trong câu trả lời phải có nguồn gốc trực tiếp từ "Dữ liệu Ngữ cảnh". Không suy diễn, không thêm thắt, không bịa đặt.
                -   **TRƯỜNG HỢP KHÔNG CÓ THÔNG TIN**: Nếu "Dữ liệu Ngữ cảnh" không chứa thông tin để trả lời câu hỏi, hãy trả lời một cách lịch sự rằng: "Xin lỗi, tôi không tìm thấy thông tin về vấn đề này trong tài liệu được cung cấp."
                -   **TRƯỜNG HỢP GIAO TIẾP**: Nếu câu hỏi của người dùng chỉ là lời chào hỏi hoặc câu nói mang tính xã giao (ví dụ: "xin chào", "cảm ơn"), hãy đáp lại một cách thân thiện với vai trò là một trợ lý AI.
                -   **NGÔN NGỮ**: Sử dụng tiếng Việt có dấu, văn phong tự nhiên, lịch sự.
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