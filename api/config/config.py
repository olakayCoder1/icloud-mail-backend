import os
from datetime import timedelta

BASE_DIR=os.path.dirname(os.path.realpath(__file__))


class Config:
    SECRET_KEY='HDHAjabIHAIHKSBIy9ahhioij9J'
    SQLALCHEMY_TRACK_MODIFICATIONS=True
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=1)
    JWT_SECRET_KEY='ksjs8wuUuHujsjjsjjsmsmw'

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')  # Redis as broker
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')  # Redis as result backend



class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_ECHO=True
    SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(BASE_DIR, 'db.sqlite3' )



class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL')
    
class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_ECHO=True
    SQLALCHEMY_DATABASE_URI='sqlite://'
    SQLALCHEMY_TRACK_MODIFICATIONS=False


config_dict = {
    'dev': DevelopmentConfig ,
    'pro' : ProductionConfig ,
    'test': TestingConfig
}