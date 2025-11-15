import os

class Config:
    # Flask / general
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///minimart.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret')
    # File uploads
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = set(os.getenv('ALLOWED_IMAGE_EXTENSIONS', 'png,jpg,jpeg').split(','))

    # Mail settings (for SMTP)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')      # e.g. your Gmail address
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')      # App password or SMTP password (do NOT commit)
    NOTIFY_EMAIL = os.getenv('NOTIFY_EMAIL', os.getenv('MAIL_USERNAME'))
