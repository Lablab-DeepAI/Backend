from flask import Blueprint, request, jsonify, current_app
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
import pdfplumber
from pptx import Presentation  # To handle PowerPoint files
from app.chatbot import ask_groq

main = Blueprint('main', __name__)

# Dictionary to store uploaded content in memory
uploaded_file_content = {}

vectorizer = TfidfVectorizer(stop_words='english')

@main.route('/', methods=['GET'])
def health_check():
    return 'Server is running!'

@main.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint to upload a file (PDF, PPT, or TXT) and extract its content.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    allowed_extensions = ['.pdf', '.pptx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file and file_ext in allowed_extensions:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)

        try:
            if file_ext == '.pdf':
                # Extract text from PDF
                with pdfplumber.open(filepath) as pdf:
                    text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            elif file_ext == '.pptx':
                # Extract text from PPT
                ppt = Presentation(filepath)
                text = "\n".join([paragraph.text for slide in ppt.slides for shape in slide.shapes if hasattr(shape, "text_frame") for paragraph in shape.text_frame.paragraphs])
            elif file_ext == '.txt':
                # Extract text from TXT
                with open(filepath, 'r', encoding='utf-8') as txt_file:
                    text = txt_file.read()

            # Store the content in memory for future use
            uploaded_file_content[file.filename] = text

            return jsonify({'message': 'File uploaded successfully', 'filename': file.filename, 'content':text}), 200

        except Exception as e:
            return jsonify({'error': f"Failed to process the file: {str(e)}"}), 500

    return jsonify({'error': f'Invalid file type, only {allowed_extensions} are allowed'}), 400


@main.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle chatbot queries.
    Expects JSON input with 'question' and 'filename' keys.
    """
    data = request.json
    question = data.get('question')
    filename = data.get('filename')

    if not question or not filename:
        return jsonify({"error": "Both 'question' and 'filename' are required"}), 400

    # Retrieve the content of the uploaded file from the file itself
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": f"File '{filename}' not found"}), 404

    try:
        # Check if content is already in memory
        if filename in uploaded_file_content:
            content = uploaded_file_content[filename]
        else:
            # Reload content from the file if not in memory
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext == '.pdf':
                with pdfplumber.open(file_path) as pdf:
                    content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            elif file_ext == '.pptx':
                ppt = Presentation(file_path)
                content = "\n".join([paragraph.text for slide in ppt.slides for shape in slide.shapes if hasattr(shape, "text_frame") for paragraph in shape.text_frame.paragraphs])
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as txt_file:
                    content = txt_file.read()
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

        # Use the chatbot function to get an answer
        groq_response = ask_groq(question, content)

        if "error" in groq_response:
            return jsonify({"error": groq_response["error"]}), 500

        return jsonify({
            "answer": groq_response.get("answer"),
            "confidence": groq_response.get("confidence")
        })

    except Exception as e:
        return jsonify({'error': f"Failed to process the file: {str(e)}"}), 500
    

def add_documents():
    return ''

def get_documents():
    #get files from vector db
    return ''


@main.route('/resources', methods=['POST'])
def recommend_based_on_bandwidth():
    try:
        user_bandwidth = request.json['bandwidth'] 

        if user_bandwidth <= 500: 
            content_type = 'text'
        elif user_bandwidth <= 2000:  
            content_type = 'media'
        else: 
            content_type = 'heavy_media'

        documents = get_documents()

        # Filter documents based on content type (size or media)
        filtered_documents = []
        for doc in documents:
            doc_id, title, content, vector = doc
            content_length = len(content.split()) 

            # Filter based on user bandwidth
            if content_type == 'text' and content_length <= 500: 
                filtered_documents.append({'name': title, 'url': f'/uploads/{doc_id}.txt'})
            elif content_type == 'media' and content_length > 500 and content_length <= 1500:  
                filtered_documents.append({'name': title, 'url': f'/uploads/{doc_id}.txt'})
            elif content_type == 'heavy_media' and content_length > 1500: 
                filtered_documents.append({'name': title, 'url': f'/uploads/{doc_id}.txt'})
        
        return jsonify(filtered_documents)

    except Exception as e:
        return jsonify({'error': str(e)}), 500