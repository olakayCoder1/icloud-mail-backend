from celery import Celery

def make_celery(app):
    # Set up Celery configuration from the Flask app's configuration
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )

    # Use the Flask app's config for Celery
    celery.conf.update(app.config)
    return celery
