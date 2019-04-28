import base64
import json
import requests
import os
from flask import current_app as app


def commit_file(path, content):
    url = app.config['WEBSITE_CONTENTS'] + path
    return requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']),
                        data=json.dumps({'message': 'post to ' + path, 'content': b64(content)}))


def b64(s):
    return base64.b64encode(s.encode()).decode()
