import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'mock_server.db'
    WIREMOCK_URL = os.environ.get('WIREMOCK_URL') or 'http://localhost:8080'
    WIREMOCK_ADMIN_API = f'{WIREMOCK_URL}/__admin'
