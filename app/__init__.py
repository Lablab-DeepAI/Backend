from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'app', 'uploads')

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)
    return app
