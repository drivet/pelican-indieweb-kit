import mf2util
from pelican import signals

from ronkyuu import sendWebmention
import requests
import os
import base64
import json
import time
import yaml


WEBSITE = 'website'
WEBSITE_CONTENTS = 'https://api.github.com/repos/drivet/' + WEBSITE + '/contents/content/'

BRIDGY_ENDPOINT = r'https://brid.gy/publish/webmention'
PUBLISH_TARGETS = [r'https://brid.gy/publish/twitter']

articles_to_syndicate = []
syndicated_articles = []


class Webmentions(object):
    def __init__(self):
        self.likes = []
        self.replies = []
        self.reposts = []


def fix_metadata(generator, metadata):
    if 'mp_syndicate_to' not in metadata:
        metadata['mp_syndicate_to'] = []
    else:
        metadata['mp_syndicate_to'] = metadata['mp_syndicate_to'].split(',')

    if 'syndication' not in metadata:
        metadata['syndication'] = []
    else:
        metadata['syndication'] = metadata['syndication'].split(',')


def find_articles_to_syndicate(generator):
    for article in list(generator.articles):
        # skip if we do not want to syndicate, or we have already syndicated
        if not article.mp_syndicate_to or article.syndication:
            continue

        for syndicate_target in [t for t in article.mp_syndicate_to if t in PUBLISH_TARGETS]:
            source_url = generator.settings['SITEURL'] + '/' + article.url
            if article.category == 'notes':
                syndicate_target += '?bridgy_omit_link=true'
            articles_to_syndicate.append([source_url, syndicate_target, article])


def syndicate(p):
    for link in articles_to_syndicate:
        source_url = link[0]
        syndicate_target = link[1]
        article = link[2]
        r = send_webmention(source_url, syndicate_target)
        if r and r.status_code == requests.codes.created:
            bridgy_response = r.json()
            article.syndication.append(bridgy_response['url'])

        if article.syndication:
            syndicated_articles.append(article)


def send_webmention(source_url, target_url):
    print('preparing to send webmention from ' + source_url + ' to ' + target_url)
    print('waiting for ' + source_url + ' to be accessible...')
    if not wait_for_url(source_url):
        print(source_url + ' is not accessible.  Skipping webmention')
        return None
    print('sending web mention from ' + source_url + " to " + target_url + " using " + BRIDGY_ENDPOINT)
    r = sendWebmention(source_url, target_url, BRIDGY_ENDPOINT)
    if r.status_code != requests.codes.created:
        print('Bridgy webmention failed with ' + str(r.status_code))
        print('Error information ' + str(r.json()))
    return r


def save_syndication(p):
    for article in syndicated_articles:
        path = os.path.relpath(article.source_path, p.settings['PATH'])
        url = WEBSITE_CONTENTS + path
        fetch_response = requests.get(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']))

        if not fetch_response.ok:
            raise Exception('failed to fetch ' + url + ' from github, code: ' + str(fetch_response.status_code))

        response = fetch_response.json()
        contents = b64decode(response['content'])
        pieces = contents.split('\n\n', 1)
        new_contents = pieces[0] + '\nsyndication: ' + ','.join(article.syndication) + '\n\n' + pieces[1]
        put_response = requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']),
                                    data=json.dumps({'message': 'post to ' + path,
                                                     'content': b64encode(new_contents),
                                                     'sha': response['sha']}))
        if not put_response.ok:
            raise Exception('failed to put article ' + url + ' on github, code: ' + str(put_response.status_code))


def b64decode(s):
    return base64.b64decode(s.encode()).decode()


def b64encode(s):
    return base64.b64encode(s.encode()).decode()


def wait_for_url(url):
    timeout_secs = 15
    wait_secs = 1
    started = time.time()

    done = False
    found = False
    while not done:
        print('requesting head from ' + url)
        r = requests.head(url)
        if r.ok:
            print('found head from ' + url)
            done = True
            found = True
        elif (time.time() - started) >= timeout_secs:
            print('timeout for ' + url)
            done = True
            found = False
        else:
            print('sleeping...', flush=True)
            time.sleep(wait_secs)
    return found


def setup_webmentions(generator, metadata):
    metadata['webmentions'] = Webmentions()


def process_webmentions(generator):
    for article in list(generator.articles):
        webmentions_path = os.path.join(generator.settings['PATH'],
                                        generator.settings['WEBMENTION_PATH'],
                                        article.slug)
        if not os.path.isdir(webmentions_path):
            continue

        for filename in os.listdir(webmentions_path):
            webmention = load_webmention(os.path.join(webmentions_path, filename))
            if webmention:
                attach_webmention(article, webmention)


def attach_webmention(article, wm):
    comment = mf2util.interpret_comment(wm['parsedSource'], wm['sourceUrl'], [wm['targetUrl']])
    comment_type = comment['comment_type'][0]
    if comment_type == 'like':
        article.webmentions.likes.append(comment)
    elif comment_type == 'repost':
        article.webmentions.reposts.append(comment)
    elif comment_type == 'reply':
        article.webmentions.replies.append(comment)
    else:
        print('Unrecognized comment type: ' + comment_type)


def load_webmention(filename):
    with open(filename) as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print("Trouble opening YAML file " + filename + ', error = ' + str(exc))
            return None


def register():
    signals.article_generator_context.connect(fix_metadata)
    signals.article_generator_finalized.connect(find_articles_to_syndicate)
    signals.finalized.connect(syndicate)
    signals.finalized.connect(save_syndication)

    signals.article_generator_context.connect(setup_webmentions)
    signals.article_generator_finalized.connect(process_webmentions)
