# -*- coding: utf-8 -*-
# ./bin/test -s plone.importexport -t test_importexportview

"""Setup tests for this package."""
from plone.importexport.testing import PLONE_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from plone import api
from plone.importexport.exceptions import ImportExportError
from plone.importexport import utils
from plone import api
import unittest2 as unittest
from zope.component import getMultiAdapter
from cStringIO import StringIO
import hashlib
import fnmatch
import os

def compare_files(a,b):
    # create hash and compare
    fileA = hashlib.sha256(a.read()).digest()
    fileB = hashlib.sha256(b.read()).digest()
    if fileA == fileB:
        return True
    else:
        return False

class TestData():

    def __init__(self):
        # FIXME find a better way to get to the testzip location
        # test zip file
        testzip = ['..', '..', 'src', 'plone', 'importexport',
         'tests', 'ImportExportTest.zip']
        zipfile = os.sep.join(testzip)
        self.zip = open(zipfile, 'r')
        self.data = [
            {'version': u'current', 'text': {u'download': u'ImportExportTest/front-page/front-page.html', u'content-type': u'text/html', u'encoding': u'utf-8'}, 'id': u'front-page', 'UID': u'cfe123705f34495995c655fa08589066', 'title': u'Plone Conference 2017, Barcelona', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Congratulations! You have successfully installed Plone.', 'expires': u'2017-06-16T23:40:00', 'path': u'ImportExportTest/front-page', 'language': u'en-us', 'effective': u'2017-06-16T23:40:00', 'rights': u'private', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Document'},
            {'version': u'current', 'id': u'news', 'UID': u'df4d14681e0f4dd6bba272f3f588b3c3', 'title': u'News', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site News', 'path': u'ImportExportTest/news', 'language': u'en-us', 'effective': u'2017-08-04T13:11:00', 'rights': u'published', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},
            {'version': u'current', 'query': [{u'i': u'portal_type', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'News Item']}, {u'i': u'review_state', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'published']}, {u'i': u'path', u'o': u'plone.app.querystring.operation.string.path', u'v': u'/'}], 'id': u'aggregator', 'UID': u'e5a5555612cb4fa9a5fd61b91f9a6e56', 'title': u'News', 'sort_on': u'effective', 'item_count': 30, '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site News', 'sort_reversed': True, 'path': u'ImportExportTest/news/aggregator', 'rights': u'published', 'customViewFields': [u'Title', u'Creator', u'Type', u'ModificationDate'], 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'limit': 1000, 'creators': [u'admin'], '@type': u'Collection'},
            {'version': u'current', 'image': {u'filename': u'58963_10200248622793289_1140334088_n.jpg', u'width': 1920, u'download': u'ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg', u'height': 1080, u'content-type': u'image/jpeg', u'size': 62002}, 'id': u'conference-website-online', 'UID': u'193ad918930843c59855c598d26bbd4a', 'title': u'Conference Website online!!', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'path': u'ImportExportTest/news/conference-website-online', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'News Item'},
            {'version': u'current', 'id': u'events', 'UID': u'bc67995f57d6474885d07b797d2d8a8e', 'title': u'Events', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Events', 'path': u'ImportExportTest/events', 'language': u'en-us', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},
            {'version': u'current', 'query': [{u'i': u'portal_type', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'Event']}, {u'i': u'review_state', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'published']}, {u'i': u'path', u'o': u'plone.app.querystring.operation.string.path', u'v': u'/'}], 'id': u'aggregator', 'UID': u'26637e4d11da4e3f9fa7fd2e7097d598', 'title': u'Events', 'sort_on': u'start', 'item_count': 30, 'relatedItems': [{u'review_state': u'published', u'title': u'Conference Website online!!', u'@type': u'News Item', u'description': u''}], '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Events', 'sort_reversed': True, 'path': u'ImportExportTest/events/aggregator', 'language': u'en-us', 'customViewFields': [u'Title', u'Creator', u'Type', u'ModificationDate'], 'created': u'2017-08-25T12:00:52+05:30', 'modified': u'2017-08-25T12:05:55+05:30', 'limit': 1000, 'creators': [u'admin'], '@type': u'Collection'},
            {'version': u'current', 'id': u'deadline-for-talk-submission', 'UID': u'21e88159f0024ba58f653f2157b9e0f5', 'title': u'Deadline for talk submission', 'start': u'2017-08-25T12:00:00+05:30', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'private', 'path': u'ImportExportTest/events/deadline-for-talk-submission', 'end': u'2017-08-25T13:00:00+05:30', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Event'},
            {'version': u'current', 'id': u'Members', 'UID': u'009c66b78c3640f1b3ad645c18f18584', 'title': u'Users', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Users', 'path': u'ImportExportTest/Members', 'language': u'en-us', 'created': u'2017-08-25T12:00:52+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},
            {'version': u'current', 'image': {u'filename': u'635861-game-wallpaper.jpg', u'width': 1366, u'download': u'ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg', u'height': 768, u'content-type': u'image/jpeg', u'size': 86670}, 'id': u'635861-game-wallpaper.jpg', 'UID': u'67f78683343443da9306e053014fc101', 'title': u'new image', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'description': u'this is the image', 'path': u'ImportExportTest/Members/635861-game-wallpaper.jpg', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Image'},
            {'version': u'current', 'file': {u'download': u'ImportExportTest/14-ist.webm/14  IST.webm', u'size': 15665887, u'content-type': u'video/webm', u'filename': u'14  IST.webm'}, 'id': u'14-ist.webm', 'UID': u'0390cf2db80642c6be65b45c7935643c', 'title': u'14  IST.webm', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'path': u'ImportExportTest/14-ist.webm', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:38+05:30', 'creators': [u'admin'], '@type': u'File'},
        ]

    def getType(self):
        type_ = []
        for data in self.data:
            type_.append(data.get('@type'))
        # unique elements
        type_ = list(set(type_))
        return type_

    def getData(self, contentType=None):

        if not contentType:
            return self.data

        for data in self.data:
            if data.get('@type')==contentType:
                return data

    def getFile(self, contentType=None):

        if not contentType:
            return StringIO(self.getData)

        return StringIO(self.getData(contentType=contentType))

    def getzip(self):
        return self.zip


class TestImportExportView(unittest.TestCase):
    """Test importexport view methods."""

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""

        self.data = TestData()
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['file'] = self.data.getzip()
        self.request['method'] = 'POST'
        self.view = getMultiAdapter((self.portal, self.request),
            name="import-export")

    def test_template_renders(self):
        results = self.view()
        # XXX: Check some string from this template
        self.assertIn("Select a CSV or a ZIP file providing the contents to import.", results)

    def test_exclude_attributes(self):

        excluded_attributes = self.view.getExcludedAttributes()

        data = {k: 1 for k in excluded_attributes}

        self.view.exclude_attributes(data)

        for key in excluded_attributes:
            # XXX: asertNotIn not present
            if key in data.keys():
                self.fail("%s key should not be present" % key)

    def test_createcontent(self):

        # get json data to create new context
        log = self.view.createcontent(self.data.getData())

        if fnmatch.fnmatch(log, 'Error'):
            self.fail("Failed in creating content")

    def test_deserialize(self):

        for data in self.data.getData():
            obj = self.view.getobjcontext(data.get('path').split(os.sep))
            if obj:
                log = self.deserialize(obj, data)
            else:
                self.fail("Error in fetching Parent object")

            if fnmatch.fnmatch(log, 'Error'):
                self.fail("Failed in deserializing")


    def test_serialize(self):

        results = self.view.serialize(self.portal)

        # XXX: Validate results
        self.assertIn('@type', results)

    def test_export(self):

        try:
            # return a string of zip file
            export = self.view.export()
            # creating a file-like object
            export = StringIO(export)
        except Exception as e:
            self.fail(e)

            # Compare exported zip and test_import
            # if not compare_files(export, self.zip):
            #     self.fail("import export files didn't match")

    def test_getExistingpath(self):

        # XXX: Assign some object to obj
        obj = None

        # get existing path under this object, may be after desearialiation

    def test_getCommanpath(self):

        # get json data to create new context
        pass

    def test_getCommancontent(self):

        # get json data to create new context
        pass

    def test_getobjcontext(self):

        # get json data to create new context
        pass

    def requestFile(self):

        # get json data to create new context
        pass

    def test_import(self):

        # FIXME obj.invokeFactory throws Unauthorized Exception
        with api.env.adopt_roles(['Manager']):
            try:
                errors = self.view.imports()
            except Exception as e:
                self.fail("Exception in imports")

    def getheaders(self):

        # get json data to create new context
        pass

    def getmatrix(self):

        # get json data to create new context
        pass

    def getExportfields(self):

        # get json data to create new context
        pass

    def getImportfields(self):

        # get json data to create new context
        pass


# class TestUtils(unittest.TestCase):
#
#     def setup(self):
#         self.Pipeline = utils.Pipeline()
#         self.mapping = utils.mapping()
#         self.InMemoryZip = utils.InMemoryZip()
#         self.fileAnalyse = utils.fileAnalyse()
#
#     def test_fileanalyse(self):
#         pass
#
#     def test_mapping(self):
#         pass
#
#     def test_pipeline(self):
#         pass
#
#     def test_memzip(self):
#         pass
