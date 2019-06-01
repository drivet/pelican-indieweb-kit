import re

from pelican_webmention.cache import has_cached_result, get_cached_result

"""
This plugin looks through each article and decides if it needs to be syndicated via Bridgy.
If it decides yes then it adds an empty link to the article content
"""


def fix_bridgy_metadata(generator, metadata):
    if 'mp_syndicate_to' not in metadata:
        metadata['mp_syndicate_to'] = []
    else:
        metadata['mp_syndicate_to'] = metadata['mp_syndicate_to'].split(',')

    for header in generator.settings['WEBMENTIONS_CONTENT_HEADERS']:
        if header not in metadata:
            metadata[header] = None

    if 'syndication' not in metadata:
        metadata['syndication'] = []
    else:
        metadata['syndication'] = metadata['syndication'].split(',')


def bridgify_content(instance):
    publish_content = []

    # mp_syndicate_to is handled via webmentions if we use bridgy, but in general it doesn't have to be
    for target_url in instance.metadata['mp_syndicate_to']:
        save_match(target_url, instance.settings, 'BRIDGY_MP_SYNDICATE_TO_MATCH', publish_content)

    for header in instance.settings['WEBMENTIONS_CONTENT_HEADERS']:
        save_match(instance.metadata[header], instance.settings, 'BRIDGY_' + header.upper() + '_MATCH', publish_content)

    if publish_content:
        instance._content += '\n' + '\n'.join(map(make_anchor, publish_content))


def make_anchor(url):
    return '<a href="' + url + '"></a>'


def save_match(url, settings, key, publish_content):
    if not url or key not in settings:
        return

    m = find_match_dict(url, settings[key])
    if m:
        publish_content.append(m)


def find_match_dict(url, d):
    for r in d.keys():
        if re.match(r, url):
            return d[r]
    return None


def attach_bridgy_syndication(generator):
    """
    Attach a syndication value to the article metadata (if there isn't one) using the
    webmention cache file.

    Used strictly for templates - the cache is used directly to figure out if we should
    skip webmentions.
    """
    for article in list(generator.articles):
        if article.syndication:
            continue

        if not has_cached_result('/' + article.url):
            continue

        target_results = get_cached_result('/' + article.url)

        def is_syndicated_loc(v):
            return find_match_list(str(v), generator.settings['BRIDGY_SYNDICATED_LOCATIONS']) != -1

        article.syndication = list(filter(is_syndicated_loc, target_results.values()))


def find_match_list(url, items):
    for i, v in enumerate(items):
        if re.match(v, url):
            return i
    return -1
