import unittest
import ezid_api
import uuid

TEST_CREATOR = 'ezid_api.py tests'
TEST_METADATA = {
    '_target': 'http://example.org/opensociety',
    'erc.who': 'Karl Popper',
    'erc.what': 'The Open Society and Its Enemies',
    'erc.when' : '1945'
}

class EzidApiTests(unittest.TestCase):
    """Suite of tests for the EzidApi service"""

    def __create_test_id(self):
        """Create a test ID involving a random component"""
        return 'PYEZID'+ str(uuid.uuid4())[:8]

    def setUp(self):
        self.arkSession = ezid_api.ApiSession.TestSession()
        self.doiSession = ezid_api.ApiSession.TestSession(scheme='doi')
        self.ark = self.arkSession.mint()
        self.doi = self.doiSession.mint()
        # store any ids we make so we can be sure to delete them later
        self.ids = [self.ark, self.doi]

    def test_ark_mint(self):
        """Mint a new ark id and make sure the resulting string starts wtih the 'ark' scheme"""
        ark = self.arkSession.mint()
        self.assertTrue(ark.startswith(ezid_api.SCHEMES['ark']))

    def test_doi_mint(self):
        """Mint a new doi id and make sure the resulting string starts wtih the 'doi' scheme"""
        doi = self.doiSession.mint()
        self.assertTrue(doi.startswith(ezid_api.SCHEMES['doi']))

    def test_ark_create(self):
        """Create a new EzidRecord who's primary identifier follows the 'ark' scheme"""
        t_id = self.__create_test_id()
        ark = self.arkSession.create(t_id)
        self.ids.append(ark)
        self.assertEqual(ark, ezid_api.SCHEMES['ark'] + ezid_api.TEST_SHOULDER['ark'] + t_id)

    def test_doi_create(self):
        """Create a new EzidRecord who's primary identifier follows the 'doi' scheme"""
        t_id = self.__create_test_id()
        doi = self.doiSession.create(t_id)
        self.ids.append(doi)
        self.assertTrue(
            doi.startswith(
                ezid_api.SCHEMES['doi'] + ezid_api.TEST_SHOULDER['doi'] + t_id.upper()
            )
        )

    def test_delete(self):
        ark = self.arkSession.mint()
        deleteArk = self.arkSession.delete(ark)
        self.assertEqual(deleteArk, ark)

    def test_get(self):
        arkGet = self.arkSession.get(self.ark)
        self.assertEqual(arkGet['identifier'], self.ark)
        self.assertTrue('metadata' in arkGet)

    def test_modify(self):
        arkGet = self.arkSession.get(self.ark)
        updated = arkGet['metadata']['_updated']
        self.arkSession.modify(self.ark, 'dc.creator', TEST_CREATOR)
        arkGet = self.arkSession.get(self.ark)
        self.assertTrue(arkGet['metadata']['_updated'] > updated)
        self.assertEqual(arkGet['metadata']['dc.creator'], TEST_CREATOR)

    def test_scheme_setter(self):
        self.assertEqual(self.arkSession.scheme, ezid_api.SCHEMES['ark'])
        self.arkSession.setScheme('doi')
        self.assertEqual(self.arkSession.scheme, ezid_api.SCHEMES['doi'])
        self.arkSession.setScheme('ark')
        self.assertEqual(self.arkSession.scheme, ezid_api.SCHEMES['ark'])

    def test_naa_setter(self):
        self.assertEqual(self.arkSession.naa, ezid_api.TEST_SHOULDER['ark'])
        self.arkSession.setNAA(ezid_api.TEST_SHOULDER['doi'])
        self.assertEqual(self.arkSession.naa, ezid_api.TEST_SHOULDER['doi'])
        self.arkSession.setNAA(ezid_api.TEST_SHOULDER['ark'])
        self.assertEqual(self.arkSession.naa, ezid_api.TEST_SHOULDER['ark'])

    def tearDown(self):
        for i in self.ids:
            try:
                self.arkSession.delete(i)
            except:
                pass

if __name__ == '__main__':
    unittest.main()

