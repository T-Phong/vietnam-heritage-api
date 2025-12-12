"""
Main entry point để test RAG system
"""
from rag import retrieve_context
import json

from reranking import advanced_search
from rewrite import QueryRewriter


# --- VÍ DỤ THỰC TẾ ---


def main():
    rewriter = QueryRewriter()
    """Hàm main để test retrieve_context"""
    print("=" * 60)
    print("Vietnam Heritage RAG System - Test")
    print("=" * 60)

    
    
    # Test queries
    test_queries = [
        "Nguyễn Trãi là ai?",
        "Vịnh Hạ Long ở đâu?",
        "Lễ hội truyền thống Việt Nam"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] Query: {query}")
        print("-" * 60)
        
        try:
            # Gọi retrieve_context từ rag.py
            results = retrieve_context(query, k=3)
            
            # In kết quả
            for j, result in enumerate(results, 1):
                metadata = result['metadata']
                print(f"\n  Kết quả {j}:")
                print(f"    Tên: {metadata.get('ten', 'N/A')}")
                print(f"    Loại hình: {metadata.get('loai_hinh', 'N/A')}")
                print(f"    Địa điểm: {metadata.get('dia_diem', 'N/A')}")
                print(f"    Mô tả: {metadata.get('mo_ta', 'N/A')[:100]}...")
        
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
    
    print("\n" + "=" * 60)
    print("Test hoàn thành!")
    print("=" * 60)


def interactive_mode():
    rewriter = QueryRewriter()
    """Chế độ tương tác - hỏi đáp liên tục"""
    print("\n🎯 Chế độ tương tác (Gõ 'exit' để thoát)")
    print("-" * 60)
    
    while True:
        query = input("\n❓ Câu hỏi: ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("👋 Tạm biệt!")
            break
        
        if not query:
            print("⚠️  Vui lòng nhập câu hỏi!")
            continue
        
        try:
            results = rewriter.ask_with_context(query,[])
            print(f"\n📚 Tìm thấy {len(results)} kết quả:")
            
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                print(f"\n  [{i}] {metadata.get('ten', 'N/A')}")
                print(f"      📍 {metadata.get('dia_diem', 'N/A')}")
                print(f"      📝 {metadata.get('mo_ta', 'N/A')[:150]}...")
        
        except Exception as e:
            print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    import sys
    
    # Kiểm tra argument
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()
