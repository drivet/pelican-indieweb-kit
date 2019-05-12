import os

import mf2util

from pelican_webmention.util import load_yaml


class Webmentions(object):
    def __init__(self):
        self.likes = []
        self.replies = []
        self.reposts = []
        self.unclassified = []


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
            webmention = load_yaml(os.path.join(webmentions_path, filename))
            if webmention:
                attach_webmention(article, webmention)


def attach_webmention(article, wm):
    comment = mf2util.interpret_comment(wm['parsedSource'], wm['sourceUrl'], [wm['targetUrl']])
    if comment['comment_type']:
        comment_type = comment['comment_type'][0]
        if comment_type == 'like':
            article.webmentions.likes.append(comment)
        elif comment_type == 'repost':
            article.webmentions.reposts.append(comment)
        elif comment_type == 'reply':
            article.webmentions.replies.append(comment)
        else:
            print('Unrecognized comment type: ' + comment_type)
            article.webmentions.unclassified.append(comment)
    else:
        print('No comment type parsed')
        article.webmentions.unclassified.append(comment)
