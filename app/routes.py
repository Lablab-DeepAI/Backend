from flask import Blueprint, request, jsonify, current_app
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
import pdfplumber

main = Blueprint('main', __name__)

vectorizer = TfidfVectorizer(stop_words='english')

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.endswith('.pdf'):
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        try:
            with pdfplumber.open(filepath) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])
            return jsonify({'content': text}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type, only PDFs are allowed'}), 400

#Endpoint accepts a user id and returns recommended documents based on the user's activity
@main.route('/recommend_from_user', methods=['POST'])
def recommend_from_user(): 
    user_id = request.json['user_id']
    #To Do: get user activity from db for documents the user recently interacted with in db
    #compare these documents to documents in db and return ones with highest similarity 

#Endpoint accepts a document and recommends documents similar to the provided document
@main.route('/recommend_from_document', methods=['POST'])
def recommend_from_document():
    if 'document_id' in request.json:
        try: 
            document_id = request.json['document_id']
            #To Do: get content for all documents in the db and store in pandas dataframe 
            #To Do: specify query string in read_sql function below once db structure is defined
            documents_df = pd.read_sql()
            tfidf_matrix = vectorizer.fit_transform(documents_df['content'])
            # To Do: get content from db for the document with given id 
            # To Do: replace str below with the result from db
            document_content = str 
            input_document_vector = vectorizer.transform([document_content])
            cosine_similarities = cosine_similarity(input_document_vector, tfidf_matrix)
            cosine_sim_df = pd.DataFrame(cosine_similarities.T, columns=["similarity"], index=documents_df["title"])
            similar_documents = cosine_sim_df.sort_values(by="similarity", ascending=False)
            n = 10
            top_similar_movies = similar_documents.head(n)
            return top_similar_movies
        except:
            return jsonify({'error': 'Could not find recommendations'}), 400
    return jsonify({'error': 'Document Id was not provided'}), 400