from flask import Flask
from flask_restx import Api
from .celery import make_celery
from .config.config import config_dict
from .icloud.views import icloud_namespace

from flask_cors import CORS


def create_app(config=config_dict['pro']):

    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)

    # Initialize Celery
    celery = make_celery(app)


    celery.set_default()



    api = Api( 
        app , version='1.0', 
        prefix= '/api/v1',
        title='ICLOUD EMAIL SENDER SCRAPE API', 
        description='A simple  API', 
        license_url='olakay', 
        contact_email='programmerolakay@gmail.com', 
        contact_url='olanrewajukabiru.vercel.com' , 
    )
    
    api.add_namespace(icloud_namespace , path='/email')


    return app , celery