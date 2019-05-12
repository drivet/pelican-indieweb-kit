import base64
import json
import os

import requests
import yaml

from pelican_webmention.util import load_yaml

cache = None
modified = False


def initialize_webmention_cache(pelican):
    global cache
    cache = load_yaml(pelican.settings['WEBMENTIONS_CACHE_FILE'])
    if cache is None:
        cache = {
            'excluded_domains': [],
            'results': {}
        }


def get_cached_results():
    return cache['results']


def get_cached_result(source_url):
    return cache['results'][source_url]


def has_cached_result(source_url):
    return source_url in cache['results']


def set_cached_result(source_url, target_results):
    cache['results'][source_url] = target_results
    global modified
    modified = True


def get_cached_excluded_domains():
    return cache['excluded_domains']


def has_excluded_domain(domain):
    return domain in cache['excluded_domains']


def add_excluded_domain(domain):
    cache['excluded_domains'].append(domain)
    global modified
    modified = True


def save_webmention_cache(pelican):
    global cache, modified

    if not modified:
        return

    url = pelican.settings['WEBSITE_GITHUB_CONTENTS_URL'] + '/' + pelican.settings['WEBMENTIONS_CACHE_FILE']

    sha = None
    fetch_response = requests.get(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']))
    if fetch_response.ok:
        sha = fetch_response.json()['sha']

    print('saving file at ' + url)
    put_data = {
        'message': 'post to ' + url,
        'content': b64encode(yaml.dump(cache))
    }
    if sha:
        put_data['sha'] = sha

    response = requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']), data=json.dumps(put_data))
    if not response.ok:
        raise Exception('failed to put article ' + url + ' on github, code: ' + str(response.status_code))


def dump_webmention_cache(pelican):
    global cache, modified

    if not modified:
        return

    url = pelican.settings['WEBSITE_GITHUB_CONTENTS_URL'] + '/' + pelican.settings['WEBMENTIONS_CACHE_FILE']

    print('saving file at ' + url)
    put_data = {
        'message': 'post to ' + url,
        'content': b64encode(yaml.dump(cache))
    }
    print('file data: ' + str(yaml.dump(cache)))
    print('save data: ' + str(put_data))


def b64decode(s):
    return base64.b64decode(s.encode()).decode()


def b64encode(s):
    return base64.b64encode(s.encode()).decode()
