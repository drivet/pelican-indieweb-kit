from flask import Flask
from app.media import media_bp
from app.micropub import micropub_bp


app = Flask(__name__)
app.config.from_envvar('INDIEWEB_SETTINGS')
app.register_blueprint(media_bp, url_prefix='/micropub/media')
app.register_blueprint(micropub_bp, url_prefix='/micropub')
