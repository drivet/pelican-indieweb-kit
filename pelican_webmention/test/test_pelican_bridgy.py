import unittest

from pelican_webmention import bridgify_content


class Instance(object):
    def __init__(self):
        self.settings = {}
        self.metadata = {}
        self._content = None


class TestPelicanBridgy(unittest.TestCase):

    def test_mp_syndicate_inserts_bridgy_links(self):
        instance = Instance()
        instance.settings = {
            'BRIDGY_MP_SYNDICATE_MATCH': {
                '^twitter_bridgy_no_link$': 'https://brid.gy/publish/twitter?bridgy_omit_link=true',
                '^twitter_bridgy$': 'https://brid.gy/publish/twitter',
                '^something$': 'https://hello.there'
            }
        }

        instance.metadata = {
            'mp_syndicate_to': 'twitter_bridgy_no_link,something'
        }
        instance._content = 'hi there'

        bridgify_content(instance)
        self.assertEqual('hi there\n' +
                         '<a href="https://brid.gy/publish/twitter?bridgy_omit_link=true"></a>\n' +
                         '<a href="https://hello.there"></a>', instance._content)

    def test_like_of_inserts_bridgy_links(self):
        instance = Instance()
        instance.settings = {
            'BRIDGY_LIKE_OF_MATCH': {
                'https://twitter/(.*)': 'https://brid.gy/publish/twitter',
            }
        }

        instance.metadata = {
            'like_of': 'https://twitter/status/1234'
        }
        instance._content = 'hi there'

        bridgify_content(instance)
        self.assertEqual('hi there\n' +
                         '<a href="https://brid.gy/publish/twitter"></a>', instance._content)

    def test_repost_of_inserts_bridgy_links(self):
        instance = Instance()
        instance.settings = {
            'BRIDGY_REPOST_OF_MATCH': {
                'https://twitter/(.*)': 'https://brid.gy/publish/twitter',
            }
        }

        instance.metadata = {
            'repost_of': 'https://twitter/status/1234'
        }
        instance._content = 'hi there'

        bridgify_content(instance)
        self.assertEqual('hi there\n' +
                         '<a href="https://brid.gy/publish/twitter"></a>', instance._content)


if __name__ == '__main__':
    unittest.main()
