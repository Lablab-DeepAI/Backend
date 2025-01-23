import os
import pdfplumber

def save_uploaded_file(file, folder_name):
    """
    Save a single uploaded file and extract text if it's a PDF.
    """
    if file.filename == '':
        raise ValueError("No file provided")

    # Save the file in the upload folder
    upload_folder = os.path.join('app/uploads', folder_name)
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    # If the file is a PDF, extract its text
    if file.filename.lower().endswith('.pdf'):
        content = extract_text_from_pdf(file_path)
    else:
        raise ValueError("Only PDF files are supported.")

    return file.filename, content

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using pdfplumber.
    """
    try:
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + '\n'
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return 'Error extracting text from this file.'
