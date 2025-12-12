from sentence_transformers import CrossEncoder

from helper import format_metadata_list_to_context
from rag import retrieve_context

# Load model Reranker (nhẹ, chạy CPU được)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def advanced_search(query, keyword):
    result = []
    for r in keyword:
        result +=retrieve_context(r.lower(), k=10)
    # 1. Bước làm sạch (Query Rewriting)
    pairs_to_score = []
    # 3. Bước lọc tinh (Reranking)
    # Tạo cặp (Câu hỏi, Đoạn văn) để chấm điểm
    for item in result:
            # --- KỸ THUẬT QUAN TRỌNG: TEXT CONSTRUCTION ---
            # Ghép các trường JSON lại thành một đoạn văn có nghĩa để model hiểu
            # Nếu chỉ đưa 'content' thì model sẽ thiếu ngữ cảnh (không biết dân tộc nào)
            constructed_text = (
                f"tên: {item['metadata'].get('ten', '').lower()}. "
                f"mô tả: {item['metadata'].get('mo_ta', '').lower()}. "
            )
            #print("constructed_text",constructed_text)
            #print("\n")
            # --- KỸ THUẬT QUAN TRỌNG: TEXT CONSTRUCTION ---
            pairs_to_score.append([query.lower(), constructed_text])
            
    scores = reranker.predict(pairs_to_score)
    #print("scores",scores,item['metadata'].get('ten', ''))
    # Gán điểm và sắp xếp lại
    for i, doc in enumerate(result):
        doc['rerank_score'] = scores[i]
        
    # Sắp xếp giảm dần theo điểm Rerank
    sorted_docs = sorted(result, key=lambda x: x['rerank_score'], reverse=True)
    
    # Lấy Top K tốt nhất
    return format_metadata_list_to_context(sorted_docs[:5])