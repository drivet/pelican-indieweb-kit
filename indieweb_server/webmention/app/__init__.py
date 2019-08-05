from flask import Flask
from indieweb_server.webmention import webmention_bp


app = Flask(__name__)
app.config.from_envvar('INDIEWEB_SETTINGS')
app.register_blueprint(webmention_bp, url_prefix='/webmention')
