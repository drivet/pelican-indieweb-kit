from pelican import signals

from pelican_webmention.bridgy import attach_bridgy_syndication, bridgify_content, fix_bridgy_metadata
from pelican_webmention.cache import initialize_webmention_cache, save_webmention_cache, dump_webmention_cache
from pelican_webmention.send_webmentions import find_articles_to_webmention, send_all_webmentions
from pelican_webmention.load_webmentions import setup_webmentions, process_webmentions


def register():
    # when pelican starts
    signals.initialized.connect(initialize_webmention_cache)

    # when article metadata has been read
    signals.article_generator_context.connect(setup_webmentions)
    signals.article_generator_context.connect(fix_bridgy_metadata)
    signals.page_generator_context.connect(fix_bridgy_metadata)
    signals.static_generator_context.connect(fix_bridgy_metadata)

    # when content is being loaded for an article/page
    signals.content_object_init.connect(bridgify_content)

    # articles have been loaded and converted to HTML
    signals.article_generator_finalized.connect(attach_bridgy_syndication)
    signals.article_generator_finalized.connect(process_webmentions)
    signals.article_generator_finalized.connect(find_articles_to_webmention)

    # pelican has finished writing and is about to close down
    signals.finalized.connect(send_all_webmentions)
    signals.finalized.connect(save_webmention_cache)
    # signals.finalized.connect(dump_webmention_cache)
