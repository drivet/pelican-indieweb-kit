import base64
import json
import os

import requests


def commit_file(url, content):
    return requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']),
                        data=json.dumps({'message': 'post to ' + url, 'content': b64(content)}))


def b64(s):
    return base64.b64encode(s.encode()).decode()
