"""
Ghost Identity Protection System Backend
Main application package with Flask factory pattern
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configure CORS with specific settings
    CORS(app, 
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ghost_identity_db.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Azure AI Configuration
    app.config['AZURE_VISION_ENDPOINT'] = os.getenv('AZURE_VISION_ENDPOINT')
    app.config['AZURE_VISION_KEY'] = os.getenv('AZURE_VISION_KEY')
    app.config['AZURE_OPENAI_ENDPOINT'] = os.getenv('AZURE_OPENAI_ENDPOINT')
    app.config['AZURE_OPENAI_KEY'] = os.getenv('AZURE_OPENAI_KEY')
    app.config['AZURE_OPENAI_DEPLOYMENT'] = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.vault import vault_bp
    from app.api.verification import verification_bp
    from app.api.notifications import notifications_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(notifications_bp)
    
    return app