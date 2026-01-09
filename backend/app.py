"""
Ghost Identity Protection System - Main Application Entry Point
"""
from flask import Flask
from flask_cors import CORS
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)