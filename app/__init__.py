from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load environment variables from the .env file in the main folder
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'app', 'uploads')

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
