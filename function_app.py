import azure.functions as func
from src.app import app as flask_app 

app = func.WsgiFunctionApp(
    app=flask_app.wsgi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS
)