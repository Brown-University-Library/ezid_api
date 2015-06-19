from datetime import datetime
import re
import requests

version = '0.3'
apiVersion = 'EZID API, Version 2'

EZID_SERVER = "https://ezid.cdlib.org"
TEST_USERNAME = 'apitest'
TEST_PASSWORD = 'apitest'
SCHEMES = {'ark': 'ark:/', 'doi': "doi:"}
STATUS_RESERVED = "reserved"
STATUS_PUBLIC = "public"
STATUS_UNAVAILABLE = "unavailable"
TEST_SHOULDER = {SCHEMES['ark'] : '99999/fk4', SCHEMES['doi'] : '10.5072/FK2'}
TEST_METADATA = {'_target': 'http://example.org/opensociety', 'erc.who': 'Karl Popper', 'erc.what': 'The Open Society and Its Enemies', 'erc.when' : '1945'}


class ApiSession ():
    ''' The ApiSession optionally accepts an EZID API username and password. 

    Also accepts a scheme (either "ark" or "doi"), and a assigning authority number.
    Defaults to test account on with scheme and prefix: ark:/99999/fk4
    '''
    def __init__(self, username=TEST_USERNAME, password=TEST_PASSWORD, scheme="ark", naa=''):
        if username == TEST_USERNAME:
            password = TEST_PASSWORD
            self.test = True
        else:
            self.test = False
        session = requests.Session()
        session.auth = (username, password)
        session.headers.update({"Content-Type": "text/plain; charset=UTF-8"})
        self.server = EZID_SERVER
        self.session = session
        # TODO: check login before returning?
        # TODO: what happens if no connection?
        self.setScheme(scheme[0:3])
        # if we are testing, use the test shoulder for the given scheme
        if self.test == True:
            naa = TEST_SHOULDER[self.scheme]
        self.setNAA(naa)

    def __parseOrReturnError(self, r):
        if r.ok:
            return self.__parseRecord(r.text)
        return r.text

    @property
    def mint_url(self):
        shoulder = self.scheme + self.naa
        return '/'.join([self.server, 'shoulder', shoulder])

    def id_url(self, identifier):
        if not identifier.startswith(SCHEMES['doi']) and not identifier.startswith(SCHEMES['ark']):
            identifier = self.scheme + self.naa + identifier
        return '/'.join([self.server, 'id', identifier])

    # Core api calls

    def mint(self, metadata={}):
        ''' Generates and registers a random identifier using the id scheme and name assigning authority already set.
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        Minted identifiers are always created with a status of "reserved".
        '''
        metadata['_status'] = STATUS_RESERVED
        anvlData = self.__makeAnvl(metadata)
        r = self.session.post(self.mint_url, data=anvlData)
        return self.__parseOrReturnError(r)

    def create(self, identifier, metadata={}):
        '''
        Optionally, metadata can be passed to the 'metadata' prameter as a dictionary object of names & values.
        '''
        if not "_status" in metadata:
            metadata["_status"] = STATUS_RESERVED
        anvlData = self.__makeAnvl(metadata)
        r = self.session.put(self.id_url(identifier), data=anvlData)
        return self.__parseOrReturnError(r)

    def modify(self, identifier, name, value):
        ''' Accepts an identifier string, a name string and a value string.
        Writes the name and value as metadata to the provided identifer. 

        The EZID system will store any name/value pair as metadata, but certian
        names have specific meaning to the system. Some names fit in the
        metadata profiles explicitly supported by the system, others are
        reserved as internal data fields.

        Reserved data fields control how EZID manages an identifer. These
        fields begin with an '_'. More here:
            http://n2t.net/ezid/doc/apidoc.html#internal-metadata

        To write to the standard EZID metadata fields use name strings of the
        form [profile].[field] where [profile] is one of 'erc', 'dc', or
        'datacite'.
        Example name strings:
          'erc.who'
          'erc.what'
          'erc.when'
          'dc.creator'
          'dc.title'
          'datacite.creator'
          'datacite.title'
          'datacite.publicationyear'
        '''
        anvlData = self.__makeAnvl({name: value})
        r = self.session.post(self.id_url(identifier), data=anvlData)
        return self.__parseOrReturnError(r)

    def get(self, identifier):
        r = self.session.get(self.id_url(identifier))
        return self.__parseOrReturnError(r)

    def delete(self, identifier):
        method = lambda: 'DELETE'
        r = self.session.delete(self.id_url(identifier))
        return self.__parseOrReturnError(r)


    # Public utility functions
    def changeProfile(self, identifier, profile):
        ''' Accepts an identifier string and a profile string where the profile string 
            is one of 'erc', 'datacite', or 'dc'.
            Sets default viewing profile for the identifier as indicated.
        '''
        # profiles = ['erc', 'datacite', 'dc']
        self.modify(identifier, '_profile', profile)

    def getStatus(self, identifier):
        return self.get(identifier)['metadata']['_status']

    def makePublic(self, identifier):
        return self.modify(identifier, '_status', STATUS_PUBLIC)

    def makeUnavailable(self, identifier):
        return self.modify(identifier, '_status', STATUS_UNAVAILABLE)

    def getTarget(self, identifier):
        return self.get(identifier)['metadata']['_target']

    def changeTarget(self, identifier, target):
        ''' Deprecated: currently an alias for modifyTarget()
        '''
        self.modifyTarget(identifier, target)

    def modifyTarget(self, identifier, target):
        ''' Accepts an identifier string and a target string.
            Changes the target url for the identifer to the string provided.
        '''
        self.modify(identifier, '_target', target)

    def getCreated(self, identifier):
        ''' Utility method for returning a datetime object instead of the unix timestamp for date created.
        '''
        return datetime.fromtimestamp(float(self.get(identifier)['metadata']['_created']))

    def getUpdated(self, identifier):
        ''' Utility method for returning a datetime object instead of the unix timestamp for date modified.
        '''
        return datetime.fromtimestamp(float(self.get(identifier)['metadata']['_updated']))

    def recordModify(self, identifier, meta, clear=False):
        ''' Accepts an identifier string, a dictionary object containing name-value pairs
            for metadata, and a boolean flag ('clear').
            Writes name value pairs to the EZID record. If clear flag is true, deletes 
            (i.e. sets to '') all names not assigned a value in the record passed in. 
            Internal EZID metadata is ignored by the clear process so, eg. '_target' or 
            '_coowner' must be overridden manually.
            Returns the record, same as get().

            Note: Because the EZID API offers no interface for full record updates, this 
            method makes an api call--through modify()--for each name-value pair updated.
        '''
        if clear:
            #TODO: clear old metadata
            oldMeta = self.get(identifier)
        for k in meta.keys():
            self.modify(identifier, k, meta[k])
        return self.get(identifier)

    def setScheme(self, scheme):
        self.scheme = SCHEMES[scheme]

    def setNAA(self, naa):
        self.naa = naa

    # Private utility functions
    def __makeAnvl(self, metadata):
        """ Accepts a dictionary object containing name value pairs 
            Returns an escaped ANVL string for submission to EZID.
        """
        if metadata == None and self.test == True:
            metadata = TEST_METADATA
        #----THIS BLOCK TAKEN WHOLESALE FROM EZID API DOCUMENTATION----#
        # http://n2t.net/ezid/doc/apidoc.html#request-response-bodies
        def escape (s):
            return re.sub("[%:\r\n]", lambda c: "%%%02X" % ord(c.group(0)), s)

        anvl = "\n".join("%s: %s" % (escape(name), escape(value)) for name, value in metadata.items()).encode("UTF-8")
        #----END BLOCK----#

        return anvl

    def __parseRecord(self, ezidResponse):
        record = {}
        parts = ezidResponse.split('\n')
        # first item is 'success: [identifier]'
        identifier = parts[0].split(': ')[1]
        metadata = {}
        if len(parts) > 1:
            for p in parts[1:]:
                pair = p.split(': ')
                if len(pair) == 2:
                    metadata[str(pair[0])] = pair[1]
            record = {'identifier' : identifier, 'metadata' : metadata}
        else:
            record = identifier
        return record


class InvalidIdentifier(Exception):
    pass
