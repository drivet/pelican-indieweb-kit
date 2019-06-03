import os

import mf2util

from pelican_webmention.util import load_yaml


all_articles = {}
all_replies = {}


class Webmentions(object):
    def __init__(self):
        self.likes = []
        self.replies = []
        self.reposts = []
        self.unclassified = []


def setup_webmentions(generator, metadata):
    metadata['webmentions'] = Webmentions()


def process_webmentions(generator):
    global all_articles
    for article in list(generator.articles):
        # keep record for later
        all_articles['/' + article.url] = article

        webmentions_path = os.path.join(generator.settings['PATH'],
                                        generator.settings['WEBMENTION_PATH'],
                                        article.slug)
        if not os.path.isdir(webmentions_path):
            continue

        for filename in os.listdir(webmentions_path):
            webmention = load_yaml(os.path.join(webmentions_path, filename))
            if webmention:
                attach_webmention(article, webmention)

    link_webmentions(generator)


def attach_webmention(article, wm):
    global all_replies
    comment = mf2util.interpret_comment(wm['parsedSource'], wm['sourceUrl'], [wm['targetUrl']])
    if comment['comment_type']:
        comment_type = comment['comment_type'][0]
        if comment_type == 'like':
            article.webmentions.likes.append(comment)
        elif comment_type == 'repost':
            article.webmentions.reposts.append(comment)
        elif comment_type == 'reply':
            all_replies[comment['url']] = comment
            article.webmentions.replies.append(comment)
        else:
            print('Unrecognized comment type: ' + comment_type)
            article.webmentions.unclassified.append(comment)
    else:
        print('No comment type parsed')
        article.webmentions.unclassified.append(comment)


# go through every article/webmention and link it to the one it's related to
def link_webmentions(generator):
    for article in list(generator.articles):
        attach_article_to_parent(article)
        for reply in article.webmentions.replies:
            attach_webmention_to_parent(reply)


def attach_webmention_to_parent(webmention):
    global all_articles
    global all_replies
    if webmention['in-reply-to']:
        for in_reply_to_dict in webmention['in-reply-to']:
            in_reply_to = in_reply_to_dict['url']
            if in_reply_to in all_articles:
                parent = all_articles[in_reply_to]
                parent.replies.append(webmention)
            elif in_reply_to in all_replies:
                parent = all_replies[in_reply_to]
                parent['replies'].append(webmention)


def attach_article_to_parent(article):
    global all_articles
    global all_replies
    if article.in_reply_to:
        if article.in_reply_to in all_articles:
            parent = all_articles[article.in_reply_to]
            parent.replies.append(article)
        elif article.in_reply_to in all_replies:
            parent = all_replies[article.in_reply_to]
            parent['replies'].append(article)

