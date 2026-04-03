import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super_secret_key_123')
    
    # Database Settings
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'adhd_dyslexia')
    
    import pymysql
    try:
        pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8"
        SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'charset': 'utf8'}}
    except Exception:
        print("\n[WARNING] MySQL Database is NOT running (WAMP offline). Falling back to local SQLite database so the app can run immediately!\n")
        SQLALCHEMY_DATABASE_URI = "sqlite:///local_fallback.db"
        SQLALCHEMY_ENGINE_OPTIONS = {}
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
