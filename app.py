"""
REST API cho Vietnam Heritage RAG System
"""
import uuid
from flask import Flask, request, jsonify
from rewrite import QueryRewriter
import os

app = Flask(__name__)

# Khởi tạo QueryRewriter (chứa ask_with_context)
rewriter = QueryRewriter()
islog = os.getenv('islog')

@app.route('/v1/chat/completions', methods=['POST'])
def ask_api():
    """
    Main endpoint - Gọi ask_with_context
    
    Request body:
    {
        "question": "Câu hỏi của bạn"
    }
    
    Response:
    {
        "question": "Câu hỏi",
        "answer": "Câu trả lời từ RAG"
    }
    """    
    try:
        data = request.get_json()
        print("data",data)
        print("islog",islog)
        all_messages = data.get("messages", [])

        history_message = all_messages[-6:-1]

        question = all_messages[-1]["content"]
        
        if not question:
            return jsonify({
                "error": "'question' cannot be empty"
            }), 400
        
        # Gọi ask_with_context
        answer = rewriter.ask_with_context(question, history_message)
        
        return jsonify({
            "id": str(uuid.uuid4()),
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": answer
                    },
                    "finish_reason": "stop"
                }
            ]
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/v1/models', methods=['GET'])
def lstmodel():
    return jsonify({
        "object": "list",
        "data": [
            {"id": "Model-1", "object": "model", "owned_by": "owner"},
            {"id": "Model-2", "object": "model", "owned_by": "owner"}
            ]
    }), 200
        

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Vietnam Heritage RAG API"
    }), 200

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        "message": "Vietnam Heritage AI REST API",
        "version": "1.0.0",
        "endpoints": {
            "POST /ask": {
                "description": "Ask a question about Vietnamese heritage",
                "body": {
                    "question": "Your question here"
                }
            },
            "GET /health": "Health check endpoint",
            "GET /": "API documentation",
            "GET /lstmodel": "List available models"
        },
        "example": {
            "url": "/ask",
            "method": "POST",
            "body": {
                "question": "Nguyễn Trãi là ai?"
            }
        }
    }), 200

@app.route('/reset', methods=['POST'])
def reset_history():
    """Reset conversation history"""
    global history
    history = []
    return jsonify({
        "message": "History reset successfully",
        "status": "success"
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(f"🚀 Vietnam Heritage RAG API")
    print("=" * 60)
    print(f"📍 Server: http://localhost:{port}")
    print(f"📝 Endpoints:")
    print(f"   POST http://localhost:{port}/ask")
    print(f"   GET  http://localhost:{port}/health")
    print(f"   GET  http://localhost:{port}/")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
