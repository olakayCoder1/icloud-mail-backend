from flask import Flask
from flask_restx import Api
from flask_migrate import Migrate

from api.icloud.models import Account, AccountConfig
from .celery import make_celery
from .config.config import config_dict
from .icloud.views import icloud_namespace
from .helpers.utils import db

from flask_cors import CORS




def create_app(config=config_dict['dev']):

    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)


    # # Initialize the database
    db.init_app(app)
    migrate = Migrate(app , db )
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

    @app.shell_context_processor
    def make_shell_context():
        return {
            'db':db,
            'Account': Account ,
            'AccountConfig': AccountConfig ,
        }
    
    return app , celery