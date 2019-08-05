import datetime
import io
import re
import os
import json

import requests
from flask import Response, Blueprint
from flask import current_app as app
from flask import request
from flask_indieauth import requires_indieauth
from werkzeug.datastructures import MultiDict

micropub_bp = Blueprint('micropub_bp', __name__)


class Photo(object):
    def __init__(self, url, alt=''):
        self.url = url
        self.alt = alt


class Entry(object):
    def __init__(self, request_data):
        self.name = extract_value(request_data, 'name')
        self.content = extract_value(request_data, 'content')

        self.updated = extract_value(request_data, 'updated')
        self.category = extract_value(request_data, 'category', True)
        self.in_reply_to = extract_value(request_data, 'in-reply-to')
        self.like_of = extract_value(request_data, 'like-of')
        self.repost_of = extract_value(request_data, 'repost-of')
        self.syndication = extract_value(request_data, 'syndication', True)
        self.mp_slug = extract_value(request_data, 'mp-slug')
        self.mp_syndicate_to = extract_value(request_data, 'mp-syndicate-to', True)

        self.published = extract_value(request_data, 'published')
        if self.published is None:
            self.published = datetime.datetime.now().isoformat()
        self.published_date = datetime.datetime.strptime(self.published, '%Y-%m-%dT%H:%M:%S.%f')

        self.photo = extract_photos(request_data)

    def __str__(self):
        return 'entry:' + self.content


def extract_photos(request_data):
    photo_req_values = extract_value(request_data, 'photo', True) or []
    photos = []
    for p in photo_req_values:
        if type(p) is dict:
            photo = Photo(p['value'], p.get('alt', ''))
        else:
            photo = Photo(p)
        photos.append(photo)
    return photos


# 1. a list of 1 is returned as a single value, unless force_multiple is True
# 2. a list with more than one value is always returned as a list
def extract_value(mdict, key, force_multiple=False):
    mkey = key + '[]'
    if mkey in mdict:
        val = mdict.getlist(mkey)
        if len(val) > 1 or force_multiple:
            return val
        else:
            return val[0]
    elif key in mdict:
        if force_multiple:
            return [mdict[key]]
        else:
            return mdict[key]
    else:
        return None


# return a date string like YYYY-MM-DD HH:MM:SS
def extract_published(entry):
    return entry.published_date.strftime('%Y-%m-%d %H:%M:%S')


def write_meta(f, meta, data):
    f.write(meta + ': ' + data + '\n')


def extract_slug(entry):
    if entry.mp_slug:
        slug = entry.mp_slug
    else:
        slug = entry.published_date.strftime('%Y%m%d%H%M%S')
    return slug


def extract_permalink(entry):
    return app.config['WEBSITE_URL'] + entry.published_date.strftime('/%Y/%m/%d/') + extract_slug(entry)


def escape_commas(s):
    return re.sub(r',', r'\,', s)


def make_note(entry):
    with io.StringIO() as f:
        write_meta(f, 'date', extract_published(entry))

        if entry.category:
            write_meta(f, 'tags', ','.join(entry.category))

        if entry.mp_syndicate_to:
            write_meta(f, 'mp_syndicate_to', ','.join(entry.mp_syndicate_to))

        if entry.like_of:
            write_meta(f, 'like_of', entry.like_of)

        if entry.repost_of:
            write_meta(f, 'repost_of', entry.repost_of)

        if entry.in_reply_to:
            write_meta(f, 'in_reply_to', entry.in_reply_to)

        if entry.photo:
            write_meta(f, 'photos', ','.join(map(lambda p: p.url, entry.photo)))
            alt = ','.join(map(lambda p: escape_commas(p.alt), entry.photo))
            if alt != ',' * (len(entry.photo) - 1):
                write_meta(f, 'photos_alt', alt)

        f.write('\n')
        if entry.content:
            f.write(entry.content)
        r = commit_file(github_commit_url('/content/notes/' + extract_slug(entry) + '.nd'), f.getvalue())
        if r.status_code != 201:
            raise Exception('failed to post to github')
    permalink = extract_permalink(entry)
    return permalink, False


def make_article(entry):
    with io.StringIO() as f:
        write_meta(f, 'title', entry.name)
        write_meta(f, 'date', extract_published(entry))

        if entry.category:
            write_meta(f, 'tags', ','.join(entry.category))

        if entry.mp_syndicate_to:
            write_meta(f, 'mp_syndicate_to', ','.join(entry.mp_syndicate_to))

        f.write('\n')
        f.write(entry.content)
        r = commit_file(github_commit_url('/content/blog/' + extract_slug(entry) + '.md'), f.getvalue())
        if r.status_code != 201:
            raise Exception('failed to post to github')
    permalink = extract_permalink(entry)
    return permalink, False


def github_commit_url(path):
    return app.config['WEBSITE_CONTENTS'] + path


def handle_query():
    print('handle query')
    q = request.args.get('q')
    if q == 'config' or q == 'syndicate-to':
        filename = app.config['MICROPUB_CONFIG']
        with open(filename) as f:
            return f.read()
    else:
        print('Could not file config file')
        return Response(status=400)


def make_form():
    json_data = request.get_json()
    if not json_data:
        return request.form
    result = MultiDict()
    result['h'] = json_data['type'][0].split('-', 1)[1]
    for key, value in json_data['properties'].items():
        result.setlist(key, value)
    return result


@micropub_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
@requires_indieauth
def handle_root():
    if 'q' in request.args:
        return handle_query()

    request_data = make_form()

    if 'h' not in request_data:
        return Response(status=400)

    if request_data['h'] == 'entry':
        entry = Entry(request_data)
        if not entry.name:
            permalink, created = make_note(entry)
        else:
            if not entry.content:
                return Response(status=400)
            permalink, created = make_article(entry)

        if created:
            resp = Response(status=201)
        else:
            resp = Response(status=202)
        resp.headers['Location'] = permalink
        return resp
    else:
        return Response(response='only h-entry supported', status=400)


def b64(s):
    return base64.b64encode(s.encode()).decode()


def commit_file(url, content):
    return requests.put(url, auth=(os.environ['USERNAME'],
                                   os.environ['PASSWORD']),
                        data=json.dumps({'message': 'post to ' + url, 'content': b64(content)}))
