import hashlib
import os
from urllib.parse import urlparse

import mf2py
import yaml
from flask import request, Response, Blueprint
from flask import current_app as app
from ronkyuu import findMentions, discoverEndpoint

from indieweb_server.util import commit_file

webmention_bp = Blueprint('webmention_bp', __name__)


@webmention_bp.route('/', methods=['POST'], strict_slashes=False)
def handle_root():
    source = request.form['source']
    target = request.form['target']

    if source == target:
        return Response(response='source URL is the same as target URL', status=400)

    if not target.startswith(app.config['WEBSITE_URL']):
        return Response(response='webmentions not supported on supplied target domain', status=400)

    if not discoverEndpoint(target)[1]:
        return Response(response='target URL does not support webmentions', status=400)

    return process_webmention(source, target)


def process_webmention(source, target):
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
    return os.path.join(app.config['WEBMENTION_FOLDER'], slug)


def webmention_path(source, target):
    folder = webmention_folder(target)
    filename = hashlib.md5(source.encode()).hexdigest()
    return os.path.join(folder, filename + '.yml')
