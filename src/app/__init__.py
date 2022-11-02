from flask import Flask
from flask_restful import Api
import secrets

app = Flask(__name__)
api = Api(app)

secret = secrets.token_urlsafe(32)
app.config['SECRET_KEY'] = secret

from src.app import routes
from src.app import functions