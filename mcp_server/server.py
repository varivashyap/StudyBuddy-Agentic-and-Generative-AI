"""
MCP Server for Study Assistant
Provides a modular API for document processing and content generation.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import StudyAssistantPipeline
from mcp_server.handlers import RequestHandler
from mcp_server.models import ModelRegistry
from mcp_server.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / 'data' / 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'mp3', 'wav', 'm4a', 'mp4'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Initialize components
model_registry = ModelRegistry()
session_manager = SessionManager()
request_handler = RequestHandler(model_registry, session_manager)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@app.route('/models', methods=['GET'])
def list_models():
    """List available models."""
    return jsonify({
        'models': model_registry.list_models()
    })


@app.route('/request-types', methods=['GET'])
def list_request_types():
    """List available request types."""
    return jsonify({
        'request_types': request_handler.list_request_types()
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a document for processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {ALLOWED_EXTENSIONS}'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = UPLOAD_FOLDER / unique_filename
        
        file.save(str(filepath))
        
        logger.info(f"File uploaded: {unique_filename}")
        
        return jsonify({
            'success': True,
            'file_id': unique_filename,
            'filename': filename,
            'filepath': str(filepath)
        })
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_document():
    """
    Process a document and generate requested content.
    
    Request body:
    {
        "file_id": "uploaded_file_id",
        "request_type": "summary|flashcards|quiz",
        "model": "default|custom_model_name",
        "parameters": {
            "query": "optional query",
            "max_items": 10,
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        file_id = data.get('file_id')
        request_type = data.get('request_type')
        model_name = data.get('model', 'default')
        parameters = data.get('parameters', {})
        
        if not file_id:
            return jsonify({'error': 'file_id is required'}), 400
        
        if not request_type:
            return jsonify({'error': 'request_type is required'}), 400
        
        # Validate file exists
        filepath = UPLOAD_FOLDER / file_id
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Process request (pass file_id for session management)
        result = request_handler.handle_request(
            file_id=file_id,
            filepath=str(filepath),
            request_type=request_type,
            model_name=model_name,
            parameters=parameters
        )

        return jsonify({
            'success': True,
            'request_type': request_type,
            'model': model_name,
            'result': result
        })

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/batch-process', methods=['POST'])
def batch_process():
    """
    Process a document with multiple request types.

    Request body:
    {
        "file_id": "uploaded_file_id",
        "requests": [
            {"type": "summary", "parameters": {...}},
            {"type": "flashcards", "parameters": {...}},
            {"type": "quiz", "parameters": {...}}
        ],
        "model": "default"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        file_id = data.get('file_id')
        requests_list = data.get('requests', [])
        model_name = data.get('model', 'default')

        if not file_id:
            return jsonify({'error': 'file_id is required'}), 400

        if not requests_list:
            return jsonify({'error': 'requests list is required'}), 400

        # Validate file exists
        filepath = UPLOAD_FOLDER / file_id
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404

        # Process all requests (reusing the same session/pipeline)
        results = {}
        for req in requests_list:
            req_type = req.get('type')
            params = req.get('parameters', {})

            try:
                result = request_handler.handle_request(
                    file_id=file_id,
                    filepath=str(filepath),
                    request_type=req_type,
                    model_name=model_name,
                    parameters=params
                )
                results[req_type] = {
                    'success': True,
                    'data': result
                }
            except Exception as e:
                logger.error(f"Error processing {req_type}: {e}")
                results[req_type] = {
                    'success': False,
                    'error': str(e)
                }

        return jsonify({
            'success': True,
            'file_id': file_id,
            'results': results
        })

    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description='Study Assistant MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    logger.info(f"Starting MCP Server on {args.host}:{args.port}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Available models: {model_registry.list_models()}")
    logger.info(f"Available request types: {request_handler.list_request_types()}")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

