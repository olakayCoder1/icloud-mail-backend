from api import create_app

app , celery = create_app()
app.app_context().push()

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(port=8000)