from flask import Blueprint, request, jsonify, current_app
from flask_restx import Api, Resource, fields
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import pdfplumber
from pptx import Presentation  # To handle PowerPoint files
from app.chatbot import ask_groq

# Initialize Flask Blueprint and API
main = Blueprint('main', __name__)
api = Api(main, version="1.0", title="File Processor API", description="API for uploading and querying files with AI support")

# Dictionary to store uploaded content in memory
uploaded_file_content = {}

vectorizer = TfidfVectorizer(stop_words='english')

# Define request and response models for Swagger
upload_model = api.model("UploadModel", {
    "file": fields.String(required=True, description="The file to upload (PDF, PPTX, or TXT)")
})

chat_model = api.model("ChatModel", {
    "question": fields.String(required=True, description="The question to ask"),
    "filename": fields.String(required=True, description="The filename of the uploaded document to query")
})


@api.route('/chat')
class Chat(Resource):
    @api.doc(description="Endpoint to handle chatbot queries based on uploaded files.")
    @api.expect(chat_model, validate=True)
    def post(self):
        data = request.json
        question = data.get('question')
        filename = data.get('filename')

        if not question or not filename:
            return jsonify({"error": "Both 'question' and 'filename' are required"}), 400

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": f"File '{filename}' not found"}), 404

        try:
            # Retrieve the content of the uploaded file
            if filename in uploaded_file_content:
                content = uploaded_file_content[filename]
            else:
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

            groq_response = ask_groq(question, content)

            if "error" in groq_response:
                return jsonify({"error": groq_response["error"]}), 500

            return jsonify({
                "answer": groq_response.get("answer"),
                "confidence": groq_response.get("confidence")
            })

        except Exception as e:
            return jsonify({'error': f"Failed to process the file: {str(e)}"}), 500


@main.route('/', methods=['GET'])
def health_check():
    return 'Server is running!'


@main.route('/upload', methods=['POST'])
@api.doc(description="Endpoint to upload a file (PDF, PPTX, or TXT) and extract its content.")
@api.expect(upload_model, validate=False)
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    allowed_extensions = ['.pdf', '.pptx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file and file_ext in allowed_extensions:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)

        try:
            if file_ext == '.pdf':
                with pdfplumber.open(filepath) as pdf:
                    text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            elif file_ext == '.pptx':
                ppt = Presentation(filepath)
                text = "\n".join([paragraph.text for slide in ppt.slides for shape in slide.shapes if hasattr(shape, "text_frame") for paragraph in shape.text_frame.paragraphs])
            elif file_ext == '.txt':
                with open(filepath, 'r', encoding='utf-8') as txt_file:
                    text = txt_file.read()

            # Store the content in memory for future use
            uploaded_file_content[file.filename] = text

            return jsonify({'message': 'File uploaded successfully', 'filename': file.filename, 'content': text}), 200

        except Exception as e:
            return jsonify({'error': f"Failed to process the file: {str(e)}"}), 500

    return jsonify({'error': f'Invalid file type, only {allowed_extensions} are allowed'}), 400


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

        filtered_documents = []
        for doc in documents:
            doc_id, title, content, vector = doc
            content_length = len(content.split())

            if content_type == 'text' and content_length <= 500:
                filtered_documents.append(doc)
            elif content_type == 'media' and 500 < content_length <= 1500:
                filtered_documents.append(doc)
            elif content_type == 'heavy_media' and content_length > 1500:
                filtered_documents.append(doc)

        return jsonify({'filtered_documents': filtered_documents}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_documents():
    # Stub: replace with actual implementation to get documents from vector DB
    return []