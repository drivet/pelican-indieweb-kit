from datetime import datetime
from urllib.parse import urlparse

import pytz
import requests
from ronkyuu import sendWebmention, findMentions

from pelican_webmention.cache import get_cached_excluded_domains, has_cached_result, \
    set_cached_result, has_excluded_domain, add_excluded_domain
from pelican_webmention.util import wait_for_url

to_webmention = {}


def find_articles_to_webmention(generator):
    utc = pytz.UTC
    from_date = utc.localize(datetime.strptime(generator.settings['WEBMENTION_FROM_DATE'], "%Y-%m-%dT%H:%M:%S"))

    for article in sorted(list(generator.articles), key=lambda a: a.date.isoformat()):

        if article.date < from_date:
            continue

        # Assume that the presence of a result means we sent webmentions before
        # TODO: look at the statuses and retry the failed ones
        if has_cached_result('/' + article.url):
            continue

        mentions = find_mentions(article, generator.settings, get_cached_excluded_domains())
        if not mentions:
            # no webmentions for this article.  Skip.
            continue

        to_webmention[mentions['post-url']] = mentions['refs']


def find_mentions(article, settings, excluded):
    source_url = settings['SITEURL'] + '/' + article.url
    mentionable_content = make_mentionable_input(article, settings['WEBMENTIONS_CONTENT_HEADERS'])
    return findMentions(source_url, None, exclude_domains=excluded, content=mentionable_content, test_urls=False)


def make_mentionable_input(article, input_headers):
    content = ''
    for header in input_headers:
        if not hasattr(article, header):
            continue
        value = getattr(article, header)
        if isinstance(value, str):
            content += make_anchor(value) + '\n'
        elif isinstance(value, list):
            for v in value:
                content += make_anchor(v) + '\n'
    return article.content + '\n' + content


def make_anchor(url):
    return '<a href="' + url + '"></a>'


class FakeRequest(object):
    def __init__(self):
        self.status_code = 204
        self.headers = {'Location': 'https://twitter.com/4444'}


def send_all_webmentions(p):
    for source_url in to_webmention.keys():
        results = {}
        excluded_domains = []
        for target_url in to_webmention[source_url]:
            print('sending webmention from ' + source_url + " to " + target_url)
            r = send_webmention(source_url, target_url)
            # r = FakeRequest()
            # r = None
            if r and r.status_code == requests.codes.created:
                results[target_url] = r.headers['Location']
            elif r:
                results[target_url] = r.status_code
            else:
                url = urlparse(target_url)
                excluded_domains.append(url.hostname)

        if results:
            set_cached_result(source_url, results)

        for excluded in excluded_domains:
            if not has_excluded_domain(excluded):
                add_excluded_domain(excluded)


def send_webmention(source_url, target_url):
    print('preparing to send webmention from ' + source_url + ' to ' + target_url)
    print('waiting for ' + source_url + ' to be accessible...')
    if not wait_for_url(source_url):
        print(source_url + ' is not accessible.  Skipping webmention')
        return None
    print('sending webmention from ' + source_url + " to " + target_url)
    r = sendWebmention(source_url, target_url)

    if not r.ok:
        print('Webmention failed with ' + str(r.status_code))
        print('Error information ' + str(r.json()))
    return r

