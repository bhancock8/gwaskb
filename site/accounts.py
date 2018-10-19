import os
from flask import Flask, render_template_string

# Use a Class-based config to avoid needing a 2nd file
# os.getenv() enables configuration through OS environment variables
class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True

def create_app():
    """ Flask application factory """
    
    # Initialize the Flask application
    app = Flask(__name__)
    app.secret_key = 'some_secret'
    
    # Setup Flask app and app.config
    app.config.from_object(__name__+'.ConfigClass')
    # Path to the upload directory
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Acceptatble extensions for upload
    app.config['ALLOWED_EXTENSIONS'] = set(['txt'])
    return app
