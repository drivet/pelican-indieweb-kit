from flask import Flask
from indieweb_server.media import media_bp
from indieweb_server.micropub import micropub_bp
from indieweb_server.webmention import webmention_bp


app = Flask(__name__)
app.config.from_envvar('INDIEWEB_SETTINGS')
app.register_blueprint(media_bp, url_prefix='/media')
app.register_blueprint(micropub_bp, url_prefix='/micropub')
app.register_blueprint(webmention_bp, url_prefix='/webmention')
