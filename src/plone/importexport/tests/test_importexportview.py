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
import json
import copy

# def compare_files(a,b):
#     # create hash and compare
#     fileA = hashlib.sha256(a.read()).digest()
#     fileB = hashlib.sha256(b.read()).digest()
#     if fileA == fileB:
#         return True
#     else:
#         return False
#
class TestData():

    def __init__(self):
        # FIXME find a better way to get to the testzip location
        # test zip file
        testzip = ['..', '..', 'src', 'plone', 'importexport',
         'tests', 'ImportExportTest.zip']
        self.zipname = os.sep.join(testzip)
        self.zip = open(self.zipname, 'r')
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

    def getzipname(self):
        return self.zipname


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

        with api.env.adopt_roles(['Manager']):
            log = self.view.createcontent(self.data.getData())

        if fnmatch.fnmatch(log, '*Error*'):
            self.fail("Failed in creating content")

    '''deserialize funciton of plone.importexport module  is highly coupled and
     thus unit case is too complex for this'''
    # def test_deserialize(self):
    #
    #     with api.env.adopt_roles(['Manager']):
    #         for data in self.data.getData():
    #             obj = self.view.getobjcontext(data.get('path').split(os.sep))
    #             if obj:
    #                 log = self.deserialize(obj, data)
    #             else:
    #                 self.fail("Error in fetching Parent object")
    #
    #             if fnmatch.fnmatch(log, '*Error*'):
    #                 self.fail("Failed in deserializing")

    def test_serialize(self):

        with api.env.adopt_roles(['Manager']):
            # it's important to inject some data
            # FIXME Require a method from unit test, which inject default Plone data at time of creation self.portal
            self.view.createcontent([self.data.getData(contentType='Folder')])
            results = self.view.serialize(self.portal)

        # XXX: Validate results
        self.assertIn('@type', json.dumps(results))

    def test_export(self):

        try:
            # return a string of zip file
            export = self.view.export()

            # creating a file-like object
            export = StringIO(export)

            f = utils.InMemoryZip()
            self.assertIn('plone.csv', f.getfiles(export))

        except Exception as e:
            self.fail(e)

    def test_requestFile(self):

        self.view.requestFile(self.data.getzip())
        # get json data to create new context
        if (self.data.getzipname()!=self.view.files.keys()[0]) or (
            self.data.getzip()!=self.view.files.values()[0]):
            self.fail()

    def test_import(self):

        with api.env.adopt_roles(['Manager']):
            log = self.view.imports()

            if fnmatch.fnmatch(log, '*Error*'):
                self.fail("Failing log for import: \n %s " %log)

    def test_getExistingpath(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            query = os.sep.join(data[0]['path'].split('/')[1:])
            self.assertIn(query, str(self.view.getExistingpath()))

    def test_getCommanpath(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            query = data[0]['path'].split('/')[1:]
            query = os.sep.join(query)
            self.assertIn(query, str(self.view.getCommonpath([data[0]['path']])))

    def test_getCommancontent(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            query = data[0]['path'].split('/')[1:]
            query = os.sep.join(query)
            self.assertIn(query, str(self.view.getCommancontent()))

    def test_getobjcontext(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            query = data[0]['path'].split('/')[1:]
            path = copy.deepcopy(query)
            path.insert(0, 'plone')
            query = os.sep.join(query)
            self.assertIn(query, str(self.view.getobjcontext(path)))

    def test_getheaders(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            headers = [
                'version', u'contributors', u'exclude_from_nav', u'subjects', u'title', u'relatedItems', '@components', 'review_state', u'description', u'expires', u'nextPreviousEnabled', u'language', u'effective', u'rights', 'created', 'modified', u'allow_discussion', u'creators'
            ]


            self.assertEqual(headers, self.view.getheaders())

    def test_getmatrix(self):

            headers = [
                'version', u'contributors', u'exclude_from_nav', u'subjects', u'title', u'relatedItems', '@components', 'review_state', u'description', u'expires', u'nextPreviousEnabled', u'language', u'effective', u'rights', 'created', 'modified', u'allow_discussion', u'creators'
            ]

            testmatrix = {0: [u'creators', u'allow_discussion', 'modified', 'created'], 1: [u'rights', u'effective', u'language', u'nextPreviousEnabled'], 2: [u'expires', u'description', 'review_state', '@components'], 3: [u'relatedItems', u'title', u'subjects', u'exclude_from_nav'], 4: [u'contributors', 'version']}

            matrix = self.view.getmatrix(headers=headers, columns=4)
            self.assertEqual(testmatrix, matrix)

    def test_getExportfields(self):

        with api.env.adopt_roles(['Manager']):

            # create content
            data = [self.data.getData(contentType="Folder")]
            self.view.createcontent(data)

            testmatrix = {0: [u'creators', u'allow_discussion', 'modified', 'created'], 1: [u'rights', u'effective', u'language', u'nextPreviousEnabled'], 2: [u'expires', u'description', 'review_state', '@components'], 3: [u'relatedItems', u'title', u'subjects', u'exclude_from_nav'], 4: [u'contributors', 'version']}

            self.assertEqual(testmatrix, self.view.getExportfields())

    def test_getImportfields(self):

        testmatrix = {u'1': [u'file', u'limit', u'customViewFields', u'effective'], u'0': [u'relatedItems', u'expires', u'start', u'end'], u'3': [u'image', u'text', u'rights', u'description'], u'2': [u'sort_reversed', u'item_count', u'sort_on', u'query'], u'5': [u'created', u'@components', u'version', u'title'], u'4': [u'review_state', u'language', u'creators', u'modified'], u'6': []}

        self.assertEqual(testmatrix, json.loads(self.view.getImportfields()))

class TestInMemoryZip(unittest.TestCase):

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):

        self.InMemoryZip = utils.InMemoryZip()
        self.data = TestData()

    def test_memzip(self):

        filename = 'added'
        filedata = 'testdata'

        self.InMemoryZip.append(filename, filedata)
        data = self.InMemoryZip.read()

        data = StringIO(data)
        zipfile = self.InMemoryZip.getfiles(data)

        self.assertEqual(filename, zipfile.keys()[0])
        self.assertEqual(filedata, zipfile.values()[0].read())

    def test_getfiles(self):

        testfiles = [
            'ImportExportTest/', 'test_folder/test.jpg', 'ImportExportTest/14-ist.webm/14  IST.webm', 'ImportExportTest/14-ist.webm/', 'ImportExportTest/news/aggregator/aggregator.html', 'ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg', 'ImportExportTest/front-page/front-page.html', 'ImportExportTest.csv', 'test_folder/', 'ImportExportTest/Members/635861-game-wallpaper.jpg/', 'ImportExportTest/test.csv/test.csv', 'ImportExportTest/Members/', 'ImportExportTest/front-page/', 'ImportExportTest/test.csv/', 'test.html', 'ImportExportTest/news/conference-website-online/', 'ImportExportTest/news/aggregator/', 'ImportExportTest/news/', 'ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg'
        ]

        files = self.InMemoryZip.getfiles(self.data.getzip())
        self.assertEqual(testfiles, files.keys())

# class TestfileAnalyse(unittest.TestCase):
#
#     layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING
#
#     def setUp(self):
#
#         self.fileAnalyse = utils.fileAnalyse()
#         self.data = TestData()
