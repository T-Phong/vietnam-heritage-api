import os
from flask import Flask, request, jsonify
from main import ask_with_context, load_dataset_and_index
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Preload models and data when the app starts (not in request handlers)
@app.before_request
def before_request():
    """Load dataset and models before first request"""
    if not hasattr(app, 'initialized'):
        logger.info("Initializing app: Loading dataset and models...")
        load_dataset_and_index()
        app.initialized = True
        logger.info("App initialization complete!")

@app.route('/ask', methods=['POST'])
def ask_api():
    """
    REST API endpoint để gọi hàm ask_with_context
    
    Request body:
    {
        "question": "Câu hỏi của bạn ở đây"
    }
    
    Response:
    {
        "answer": "Câu trả lời từ AI"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'question' not in data:
            return jsonify({
                "error": "Missing 'question' field in request body"
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                "error": "'question' cannot be empty"
            }), 400
        
        # Call the main function
        answer = ask_with_context(question)
        
        return jsonify({
            "question": question,
            "answer": answer
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy"
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "Vietnam Heritage AI API",
        "endpoints": {
            "POST /ask": "Send a question and get an answer",
            "GET /health": "Health check endpoint"
        },
        "usage": {
            "url": "/ask",
            "method": "POST",
            "body": {
                "question": "Your question here"
            }
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
