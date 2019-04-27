import hashlib
import os
import base64
import requests
import json

from flask import Flask, request, Response
from ronkyuu import findMentions, discoverEndpoint
import mf2py
from urllib.parse import urlparse
import yaml

app = Flask(__name__)

WEBMENTION_FOLDER = '/content/webmentions'

WEBSITE = 'website'
WEBSITE_CONTENTS = 'https://api.github.com/repos/drivet/' + WEBSITE + '/contents'


@app.route('/', methods=['POST'], strict_slashes=False)
def handle_root():
    source = request.form['source']
    target = request.form['target']

    if source == target:
        return Response(response='source same as target', status=400)

    if not discoverEndpoint(target)[1]:
        return Response(response='target does not support webmentions', status=400)

    # find mention in source
    result = findMentions(source, target)

    if result['status'] != 200:
        return Response(response='error fetching source', status=400)

    if not result['refs']:
        return Response(response='target not found in source', status=400)

    parsed = mf2py.Parser(url=source).to_dict()
    r = commit_file(webmention_path(source, target), yaml.dump(parsed))
    if r.status_code != 201:
        print('failed to post to github: ' + r.text)
        raise Exception('failed to post to github: ' + str(r))
    return Response(status=201)


def extract_slug(target):
    path = urlparse(target).path
    pieces = path.split('/')
    slug_with_ext = pieces[-1]
    slug = slug_with_ext.rsplit('.', 1)[0]
    return slug


def webmention_folder(target):
    slug = extract_slug(target)
    return os.path.join(WEBMENTION_FOLDER, slug)


def webmention_path(source, target):
    folder = webmention_folder(target)
    filename = hashlib.md5(source.encode()).hexdigest()
    return os.path.join(folder, filename + '.yml')


def commit_file(path, content):
    url = WEBSITE_CONTENTS + path
    return requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']),
                        data=json.dumps({'message': 'post to ' + path, 'content': b64(content)}))


def b64(s):
    return base64.b64encode(s.encode()).decode()
