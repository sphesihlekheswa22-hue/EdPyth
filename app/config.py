import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-session-key-change-in-production'))
    
    # Database - Use SQLite by default unless explicitly set
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url and (db_url.startswith('postgresql') or db_url.startswith('mysql')):
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Default to SQLite
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edumind_ai.db')
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Only use pool options for PostgreSQL
    if not SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'jpg', 'png', 'jpeg'}
    
    # NVIDIA API (for AI features)
    NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY', '')
    
    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
