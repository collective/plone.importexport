# -*- coding: utf-8 -*-
# ./bin/test -s plone.importexport -t test_importexport

"""Setup tests for this package."""
from cStringIO import StringIO
from plone import api
from plone.importexport import utils
from plone.importexport.testing import PLONE_IMPORTEXPORT_INTEGRATION_TESTING
from zope.component import getMultiAdapter

import copy
import fnmatch
import json
import os
import unittest


dir_path = os.path.dirname(os.path.realpath(__file__))


class TestData():

    def __init__(self):
        self.zipname = 'ImportExportTest.zip'
        self.zip = open(os.path.join(dir_path, self.zipname), 'r')
        self.data = [
            {'version': u'current', 'text': {u'download': u'ImportExportTest/front-page/front-page.html', u'content-type': u'text/html', u'encoding': u'utf-8'}, 'id': u'front-page', 'UID': u'cfe123705f34495995c655fa08589066', 'title': u'Plone Conference 2017, Barcelona', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Congratulations! You have successfully installed Plone.', 'expires': u'2017-06-16T23:40:00', 'path': u'ImportExportTest/front-page', 'language': u'en-us', 'effective': u'2017-06-16T23:40:00', 'rights': u'private', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Document'},  # NOQA: E501
            {'version': u'current', 'id': u'news', 'UID': u'df4d14681e0f4dd6bba272f3f588b3c3', 'title': u'News', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site News', 'path': u'ImportExportTest/news', 'language': u'en-us', 'effective': u'2017-08-04T13:11:00', 'rights': u'published', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},  # NOQA: E501
            {'version': u'current', 'text': {u'download': u'ImportExportTest/news/aggregator/aggregator.html', u'content-type': u'text/html', u'encoding': u'utf-8'}, 'query': [{u'i': u'portal_type', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'News Item']}, {u'i': u'review_state', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'published']}, {u'i': u'path', u'o': u'plone.app.querystring.operation.string.path', u'v': u'/'}], 'id': u'aggregator', 'UID': u'e5a5555612cb4fa9a5fd61b91f9a6e56', 'title': u'News', 'sort_on': u'effective', 'item_count': 30, '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site News', 'sort_reversed': True, 'path': u'ImportExportTest/news/aggregator', 'language': u'en-us', 'rights': u'published', 'customViewFields': [u'Title', u'Creator', u'Type', u'ModificationDate'], 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:24:47+05:30', 'limit': 1000, 'creators': [u'admin'], '@type': u'Collection'},  # NOQA: E501
            {'version': u'current', 'image': {u'filename': u'58963_10200248622793289_1140334088_n.jpg', u'width': 1920, u'download': u'ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg', u'height': 1080, u'content-type': u'image/jpeg', u'size': 62002}, 'id': u'conference-website-online', 'UID': u'193ad918930843c59855c598d26bbd4a', 'title': u'Conference Website online!!', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'path': u'ImportExportTest/news/conference-website-online', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'News Item'},  # NOQA: E501
            {'version': u'current', 'id': u'events', 'UID': u'bc67995f57d6474885d07b797d2d8a8e', 'title': u'Events', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Events', 'path': u'ImportExportTest/events', 'language': u'en-us', 'created': u'2017-08-25T12:00:51+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},  # NOQA: E501
            {'version': u'current', 'query': [{u'i': u'portal_type', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'Event']}, {u'i': u'review_state', u'o': u'plone.app.querystring.operation.selection.any', u'v': [u'published']}, {u'i': u'path', u'o': u'plone.app.querystring.operation.string.path', u'v': u'/'}], 'id': u'aggregator', 'UID': u'26637e4d11da4e3f9fa7fd2e7097d598', 'title': u'Events', 'sort_on': u'start', 'item_count': 30, 'relatedItems': [{u'review_state': u'published', u'title': u'Conference Website online!!', u'@type': u'News Item', u'description': u''}], '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Events', 'sort_reversed': True, 'path': u'ImportExportTest/events/aggregator', 'language': u'en-us', 'customViewFields': [u'Title', u'Creator', u'Type', u'ModificationDate'], 'created': u'2017-08-25T12:00:52+05:30', 'modified': u'2017-08-25T12:05:55+05:30', 'limit': 1000, 'creators': [u'admin'], '@type': u'Collection'},  # NOQA: E501
            {'version': u'current', 'id': u'deadline-for-talk-submission', 'UID': u'21e88159f0024ba58f653f2157b9e0f5', 'title': u'Deadline for talk submission', 'start': u'2017-08-25T12:00:00+05:30', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'private', 'path': u'ImportExportTest/events/deadline-for-talk-submission', 'end': u'2017-08-25T13:00:00+05:30', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Event'},  # NOQA: E501
            {'version': u'current', 'id': u'Members', 'UID': u'009c66b78c3640f1b3ad645c18f18584', 'title': u'Users', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'review_state': u'published', 'description': u'Site Users', 'path': u'ImportExportTest/Members', 'language': u'en-us', 'created': u'2017-08-25T12:00:52+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Folder'},  # NOQA: E501
            {'version': u'current', 'image': {u'filename': u'635861-game-wallpaper.jpg', u'width': 1366, u'download': u'ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg', u'height': 768, u'content-type': u'image/jpeg', u'size': 86670}, 'id': u'635861-game-wallpaper.jpg', 'UID': u'67f78683343443da9306e053014fc101', 'title': u'new image', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'description': u'this is the image', 'path': u'ImportExportTest/Members/635861-game-wallpaper.jpg', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:37+05:30', 'creators': [u'admin'], '@type': u'Image'},  # NOQA: E501
            {'version': u'current', 'file': {u'download': u'ImportExportTest/14-ist.webm/14  IST.webm', u'size': 15665887, u'content-type': u'video/webm', u'filename': u'14  IST.webm'}, 'id': u'14-ist.webm', 'UID': u'0390cf2db80642c6be65b45c7935643c', 'title': u'14  IST.webm', '@components': {u'breadcrumbs': {}, u'navigation': {}, u'workflow': {}}, 'path': u'ImportExportTest/14-ist.webm', 'language': u'en-us', 'created': u'2017-08-25T12:01:37+05:30', 'modified': u'2017-08-25T12:01:38+05:30', 'creators': [u'admin'], '@type': u'File'},  # NOQA: E501
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
            if data.get('@type') == contentType:
                return data

    def getFile(self, contentType=None):

        if not contentType:
            return StringIO(self.getData)

        return StringIO(self.getData(contentType=contentType))

    def getzip(self):
        self.zip.seek(0)
        return self.zip

    def getzipname(self):
        return self.zipname


class TestImportExportView(unittest.TestCase):
    """Test importexport view methods."""

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""

        self.data = TestData()
        self.context = self.layer['portal']
        self.request = self.layer['request']
        self.request['file'] = self.data.getzip()
        self.request['method'] = 'POST'
        self.view = getMultiAdapter((self.context, self.request),
                                    name='import-export')

    def test_template_renders(self):
        results = self.view()
        # XXX: Check some string from this template
        self.assertIn(
            'Select a CSV or a ZIP file providing the contents to import.',
            results)

    def test_exclude_attributes(self):

        excluded_attributes = self.view.getExcludedAttributes()

        data = {k: 1 for k in excluded_attributes}

        self.view.exclude_attributes(data)

        for key in excluded_attributes:
            # XXX: asertNotIn not present
            if key in data.keys():
                self.fail('{arg} key should not be present'.format(
                    arg=str(key)))

    def test_createcontent(self):

        with api.env.adopt_roles(['Manager']):
            log = self.view.processContentCreation(self.data.getData())

        if fnmatch.fnmatch(log, '*Error*'):
            self.fail('Failed in creating content')

    # deserialize funciton of plone.importexport module  is highly coupled and
    #  thus unit case is too complex for this
    def test_deserialize(self):

        with api.env.adopt_roles(['Manager']):
            self.view.processContentCreation(self.data.getData())
            for data in self.data.getData():
                obj = self.view.getobjcontext(data.get('path').split(os.sep))
                if obj:
                    log = self.view.deserialize(obj, data)
                else:
                    self.fail('Error in fetching Parent object')

                if fnmatch.fnmatch(log, '*Error*'):
                    self.fail('Failed deserialized log: \n {arg}'.format(
                        arg=str(log)))

    def test_serialize(self):

        with api.env.adopt_roles(['Manager']):
            # it's important to inject some data
            # FIXME Require a method from unit test,
            # which inject default Plone data at time of creation self.context
            self.view.processContentCreation([self.data.getData(contentType='Folder')])
            results = self.view.serialize(self.context)

        # XXX: Validate results
        if fnmatch.fnmatch(json.dumps(results), '*Error*'):
            self.fail('Error while serializing \n {arg}'.format(
                arg=str(results[-1])))
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
        if (self.data.getzipname() != self.view.files.keys()[0]) or (
                self.data.getzip() != self.view.files.values()[0]):
            self.fail()

    def test_import(self):

        with api.env.adopt_roles(['Manager']):
            log = self.view.imports()
            if fnmatch.fnmatch(log, '*Error*'):
                self.fail('Failing log for import: \n {arg} '.format(
                    arg=str(log)))

    def test_getExistingpath(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            query = os.sep.join(data[0]['path'].split('/')[1:])
            self.assertIn(query, str(self.view.getExistingpath()))

    def test_getCommanpath(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            query = data[0]['path'].split('/')[1:]
            query = os.sep.join(query)
            self.assertIn(query,
                          str(self.view.getCommonpath([data[0]['path']])))

    def test_getCommancontent(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            query = data[0]['path'].split('/')[1:]
            query = os.sep.join(query)
            self.assertIn(query, str(self.view.getCommancontent()))

    def test_getobjcontext(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            query = data[0]['path'].split('/')[1:]
            path = copy.deepcopy(query)
            path.insert(0, 'plone')
            query = os.sep.join(query)
            self.assertIn(query, str(self.view.getobjcontext(path)))

    def test_getheaders(self):

        with api.env.adopt_roles(['Manager']):

            # create path
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            headers = [
                'version', u'contributors', u'subjects', u'exclude_from_nav', u'title', u'is_folderish', u'relatedItems', '@components', 'review_state', u'description', u'expires', u'nextPreviousEnabled', u'effective', u'language', u'rights', 'created', 'modified', u'allow_discussion', u'creators',  # NOQA: E501
            ]
            self.assertEqual(headers, self.view.getheaders())

    def test_getmatrix(self):

            headers = [
                'version', u'contributors', u'subjects', u'exclude_from_nav', u'title', u'is_folderish',u'relatedItems', '@components', 'review_state', u'description', u'expires', u'nextPreviousEnabled',u'effective', u'language', u'rights', 'created', 'modified', u'allow_discussion', u'creators',   # NOQA: E501
            ]

            testmatrix = {0: [u'creators', u'allow_discussion', 'modified', 'created'], 1: [u'rights', u'language', u'effective', u'nextPreviousEnabled'], 2: [u'expires', u'description', 'review_state', '@components'], 3: [u'relatedItems', 'is_folderish', u'title', u'exclude_from_nav'], 4: [u'subjects', u'contributors', 'version']}  # NOQA: E501

            matrix = self.view.getmatrix(headers=headers, columns=4)
            self.assertEqual(testmatrix, matrix)

    def test_getExportfields(self):

        with api.env.adopt_roles(['Manager']):

            # create content
            data = [self.data.getData(contentType='Folder')]
            self.view.processContentCreation(data)

            testmatrix = {0: [u'creators', u'allow_discussion', 'modified', 'created'], 1: [u'rights', u'language', u'effective', u'nextPreviousEnabled'], 2: [u'expires', u'description', 'review_state', '@components'], 3: [u'relatedItems', 'is_folderish', u'title', u'exclude_from_nav'], 4: [u'subjects', u'contributors', 'version']}  # NOQA: E501
            self.assertEqual(testmatrix, self.view.getExportfields())

    def test_getImportfields(self):

        testmatrix = {u'1': [u'file', u'limit', u'customViewFields', u'effective'], u'0': [u'relatedItems', u'expires', u'start', u'end'], u'3': [u'image', u'text', u'rights', u'description'], u'2': [u'sort_reversed', u'item_count', u'sort_on', u'query'], u'5': [u'created', u'@components', u'version', u'title'], u'4': [u'review_state', u'language', u'creators', u'modified'], u'6': []}  # NOQA: E501
        self.assertEqual(testmatrix, json.loads(self.view.getImportfields()))


class TestInMemoryZip(unittest.TestCase):

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
            'ImportExportTest/',
            'test_folder/test.jpg',
            'ImportExportTest/14-ist.webm/14  IST.webm',
            'ImportExportTest/14-ist.webm/',
            'ImportExportTest/news/aggregator/aggregator.html',
            'ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg',  # NOQA: E501
            'ImportExportTest/front-page/front-page.html',
            'ImportExportTest.csv',
            'test_folder/',
            'ImportExportTest/Members/635861-game-wallpaper.jpg/',
            'ImportExportTest/test.csv/test.csv',
            'ImportExportTest/Members/',
            'ImportExportTest/front-page/',
            'ImportExportTest/test.csv/',
            'test.html',
            'ImportExportTest/news/conference-website-online/',
            'ImportExportTest/news/aggregator/',
            'ImportExportTest/news/',
            'ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg',  # NOQA: E501
        ]
        files = self.InMemoryZip.getfiles(self.data.getzip())
        self.assertEqual(testfiles, files.keys())


class TestfileAnalyse(unittest.TestCase):

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):

        self.data = TestData()
        self.context = self.layer['portal']
        self.request = self.layer['request']
        self.request['file'] = self.data.getzip()
        self.request['method'] = 'POST'
        self.view = getMultiAdapter((self.context, self.request),
                                    name='import-export')

        self.view.requestFile(self.data.getzip())
        self.fileAnalyse = utils.fileAnalyse(self.view.files)

        # self.assertEqual()

    def test_getfiles(self):

        testData = ['ImportExportTest/', 'ImportExportTest/14-ist.webm/14  IST.webm', 'ImportExportTest/test.csv/test.csv', 'ImportExportTest/news/aggregator/aggregator.html', 'ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg', 'ImportExportTest/Members/635861-game-wallpaper.jpg/', 'ImportExportTest/Members/', 'test.html', 'ImportExportTest/news/conference-website-online/', 'ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg', 'ImportExportTest/news/aggregator/', 'ImportExportTest/14-ist.webm/', 'ImportExportTest/front-page/front-page.html', 'ImportExportTest.csv', 'test_folder/', 'ImportExportTest/front-page/', 'ImportExportTest/test.csv/', 'ImportExportTest/news/', 'test_folder/test.jpg']  # NOQA: E501

        self.assertEqual(testData, self.fileAnalyse.getFiles().keys())

    def test_getCsv(self):

        testCsv = '@type,path,id,UID,version,contributors,exclude_from_nav,subjects,title,relatedItems,@components,review_state,description,expires,language,effective,rights,created,modified,allow_discussion,creators,text,nextPreviousEnabled,image,query,sort_on,sort_reversed,item_count,customViewFields,limit,event_url,file,image_caption,open_end,attendees,sync_uid,recurrence,start,location,contact_name,contact_phone,contact_email,end,whole_day\r\n"""Document""","""ImportExportTest/front-page""","""front-page""","""cfe123705f34495995c655fa08589066""","""current""","""Null""","""Null""","""Null""","""Plone Conference 2017, Barcelona""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Congratulations! You have successfully installed Plone.""","""2017-06-16T23:40:00""","""en-us""","""2017-06-16T23:40:00""","""private""","""2017-08-25T12:00:51+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]","{""download"": ""ImportExportTest/front-page/front-page.html"", ""content-type"": ""text/html"", ""encoding"": ""utf-8""}",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Folder""","""ImportExportTest/news""","""news""","""df4d14681e0f4dd6bba272f3f588b3c3""","""current""","""Null""","""Null""","""Null""","""News""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Site News""","""Null""","""en-us""","""2017-08-04T13:11:00""","""published""","""2017-08-25T12:00:51+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]",Field NA,"""Null""",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Collection""","""ImportExportTest/news/aggregator""","""aggregator""","""e5a5555612cb4fa9a5fd61b91f9a6e56""","""current""","""Null""","""Null""","""Null""","""News""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Site News""","""Null""","""en-us""","""Null""","""published""","""2017-08-25T12:00:51+05:30""","""2017-08-25T12:24:47+05:30""","""Null""","[""admin""]","{""download"": ""ImportExportTest/news/aggregator/aggregator.html"", ""content-type"": ""text/html"", ""encoding"": ""utf-8""}",Field NA,Field NA,"[{""i"": ""portal_type"", ""o"": ""plone.app.querystring.operation.selection.any"", ""v"": [""News Item""]}, {""i"": ""review_state"", ""o"": ""plone.app.querystring.operation.selection.any"", ""v"": [""published""]}, {""i"": ""path"", ""o"": ""plone.app.querystring.operation.string.path"", ""v"": ""/""}]","""effective""",true,30,"[""Title"", ""Creator"", ""Type"", ""ModificationDate""]",1000,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""News Item""","""ImportExportTest/news/conference-website-online""","""conference-website-online""","""193ad918930843c59855c598d26bbd4a""","""current""","""Null""","""Null""","""Null""","""Conference Website online!!""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Null""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:01:37+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]","""Null""",Field NA,"{""height"": 1080, ""width"": 1920, ""download"": ""ImportExportTest/news/conference-website-online/58963_10200248622793289_1140334088_n.jpg"", ""filename"": ""58963_10200248622793289_1140334088_n.jpg"", ""content-type"": ""image/jpeg"", ""size"": 62002}",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,"""Null""",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Folder""","""ImportExportTest/events""","""events""","""bc67995f57d6474885d07b797d2d8a8e""","""current""","""Null""","""Null""","""Null""","""Events""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Site Events""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:00:51+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]",Field NA,"""Null""",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Collection""","""ImportExportTest/events/aggregator""","""aggregator""","""26637e4d11da4e3f9fa7fd2e7097d598""","""current""","""Null""","""Null""","""Null""","""Events""","[{""@type"": ""News Item"", ""review_state"": ""published"", ""description"": """", ""title"": ""Conference Website online!!""}]","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Site Events""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:00:52+05:30""","""2017-08-25T12:05:55+05:30""","""Null""","[""admin""]","""Null""",Field NA,Field NA,"[{""i"": ""portal_type"", ""o"": ""plone.app.querystring.operation.selection.any"", ""v"": [""Event""]}, {""i"": ""review_state"", ""o"": ""plone.app.querystring.operation.selection.any"", ""v"": [""published""]}, {""i"": ""path"", ""o"": ""plone.app.querystring.operation.string.path"", ""v"": ""/""}]","""start""",true,30,"[""Title"", ""Creator"", ""Type"", ""ModificationDate""]",1000,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Event""","""ImportExportTest/events/deadline-for-talk-submission""","""deadline-for-talk-submission""","""21e88159f0024ba58f653f2157b9e0f5""","""current""","""Null""","""Null""","""Null""","""Deadline for talk submission""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""private""","""Null""","""Null""","""Null""","""Null""","""Null""","""2017-08-25T12:01:37+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]","""Null""",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,"""Null""",Field NA,Field NA,"""Null""","""Null""","""Null""","""Null""","""2017-08-25T12:00:00+05:30""","""Null""","""Null""","""Null""","""Null""","""2017-08-25T13:00:00+05:30""","""Null"""\r\n"""Folder""","""ImportExportTest/Members""","""Members""","""009c66b78c3640f1b3ad645c18f18584""","""current""","""Null""","""Null""","""Null""","""Users""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""published""","""Site Users""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:00:52+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]",Field NA,"""Null""",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""Image""","""ImportExportTest/Members/635861-game-wallpaper.jpg""","""635861-game-wallpaper.jpg""","""67f78683343443da9306e053014fc101""","""current""","""Null""","""Null""","""Null""","""new image""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""Null""","""this is the image""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:01:37+05:30""","""2017-08-25T12:01:37+05:30""","""Null""","[""admin""]",Field NA,Field NA,"{""height"": 768, ""width"": 1366, ""download"": ""ImportExportTest/Members/635861-game-wallpaper.jpg/635861-game-wallpaper.jpg"", ""filename"": ""635861-game-wallpaper.jpg"", ""content-type"": ""image/jpeg"", ""size"": 86670}",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n"""File""","""ImportExportTest/14-ist.webm""","""14-ist.webm""","""0390cf2db80642c6be65b45c7935643c""","""current""","""Null""","""Null""","""Null""","""14  IST.webm""","""Null""","{""breadcrumbs"": {}, ""navigation"": {}, ""workflow"": {}}","""Null""","""Null""","""Null""","""en-us""","""Null""","""Null""","""2017-08-25T12:01:37+05:30""","""2017-08-25T12:01:38+05:30""","""Null""","[""admin""]",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,"{""download"": ""ImportExportTest/14-ist.webm/14  IST.webm"", ""filename"": ""14  IST.webm"", ""content-type"": ""video/webm"", ""size"": 15665887}",Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA,Field NA\r\n'  # NOQA: E501

        self.assertEqual(testCsv, self.fileAnalyse.getCsv().read())

    def test_getFiletype(self):

        self.assertEqual('csv', self.fileAnalyse.getFiletype(
            filename='ImportExportTest/test.csv/test.csv'))


class Testmapping(unittest.TestCase):

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):

        self.context = self.layer['portal']
        self.data = TestData()
        self.mapping = utils.mapping(self)
        self.request = self.layer['request']
        self.request['file'] = self.data.getzip()
        self.request['method'] = 'POST'
        self.view = getMultiAdapter((self.context, self.request),
                                    name='import-export')

    def getobjcontext(self, path):
        return self.view.getobjcontext(path)

    def test_mapNewUID(self):

        with api.env.adopt_roles(['Manager']):
            for data in self.data.getData():
                log = self.view.processContentCreation([data])
                path = data.get('path').split('/')[1:]
                path.insert(0, 'plone')
                path = os.sep.join(path)
                data['path'] = path
                uid = data.get('UID')
                mapping = self.mapping.mapNewUID([data])

                if uid not in mapping.keys():
                    self.fail()

    def test_getUID(self):

        data = [self.data.getData(contentType='Folder')]

        with api.env.adopt_roles(['Manager']):
            log = self.view.processContentCreation(data)
            path = data[0]['path'].split('/')[1:]
            path.insert(0, 'plone')
            path = os.sep.join(path)
            uid = data[0].get('UID')

            newUID = self.mapping.getUID(path)

            if uid == newUID:
                self.fail()

    # TODO
    def test_internallink(self):

        pass
        # for data in self.data.getData():
        #     uid = data.get('UID')
        #     data = json.dumps(data)
        #     mappedData = self.mapping.internallink(data)
        #     if fnmatch.fnmatch(data, ('*'+uid+'*')):
        #         self.fail()


class TestPipeline(unittest.TestCase):

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):

        self.data = TestData()
        self.context = self.layer['portal']
        self.request = self.layer['request']
        self.request['file'] = self.data.getzip()
        self.request['method'] = 'POST'
        self.view = getMultiAdapter((self.context, self.request),
                                    name='import-export')
        self.zip = utils.InMemoryZip()
        self.view.requestFile(self.data.getzip())
        self.fileAnalyse = utils.fileAnalyse(self.view.files)
        self.pipeline = utils.Pipeline()
        self.mapping = utils.mapping(self)

    def test_getcsvheaders(self):

        testData = [
            'id',
            'UID',
            'title',
            'version',
            '@components',
            'path',
            'created',
            'modified',
            'creators',
            '@type',
            'language',
            'review_state',
            'description',
            'rights',
            'text',
            'image',
            'query',
            'sort_on',
            'item_count',
            'sort_reversed',
            'effective',
            'customViewFields',
            'limit',
            'file',
            'end',
            'start',
            'expires',
            'relatedItems',
        ]
        self.assertEqual(testData, self.pipeline.getcsvheaders(
            self.data.getData()))

    def test_convertjson(self):

        with api.env.adopt_roles(['Manager']):
            log = self.view.imports()
            exportFormat = {
                'csv': 'plone.csvPK',
                'combined': 'plone.csvPK',
                'files': 'plone/14-ist.webm/14  IST.webmPK'}
            data_list = self.view.serialize(self.context)[:-1]
            csv_headers = self.pipeline.getcsvheaders(self.data.getData())

            for formats in exportFormat.keys():
                self.request['exportFormat'] = formats
                self.zip = utils.InMemoryZip()

                self.pipeline.convertjson(obj=self, data_list=data_list,
                                          csv_headers=csv_headers)

                # self.assertEqual(self.zip.read(), exportFormat[formats])
                self.assertIn(exportFormat[formats], self.zip.read())

    def test_getblob(self):
        with api.env.adopt_roles(['Manager']):
            log = self.view.imports()
            test_dataFormat = ['Document', 'News Item']
            data_list = self.view.serialize(self.context)[:-1]

            for data in data_list:
                tempData = copy.deepcopy(data)
                if data.get('@type') in test_dataFormat:
                    for key in data.keys():
                        if not data[key]:
                            continue
                        self.pipeline.getblob(self, data[key], data['path'])
                        if tempData[key] != data[key]:
                            self.assertIn('download', data[key])

                    test_dataFormat.remove(data.get('@type'))

    def test_converttojson(self):
        csvData = '"fieldA", "fieldB", \n "A","B"'
        jsonList = [{}, {}, {}, {}, {}, {}, {}, {}, {}]
        self.assertEqual(jsonList, self.pipeline.converttojson(
            data=csvData, header='fieldB'))

    def test_jsonify(self):
        testData = {
            'description': u'Site News',
            'effective': u'2017-08-04T13:11:00',
            'path': u'ImportExportTest/news',
            'id': u'news',
            'UID': u'df4d14681e0f4dd6bba272f3f588b3c3',
            'language': u'en-us',
            'rights': u'published',
            'title': u'News',
            'modified': u'2017-08-25T12:01:37+05:30',
            'created': u'2017-08-25T12:00:51+05:30',
            'version': u'current',
            '@components': {u'breadcrumbs': {},
                u'navigation': {},
                u'workflow': {}},
            'review_state': u'published',
            'creators': [u'admin'],
            '@type': u'Folder',
        }
        self.assertEqual(
            testData,
            self.pipeline.jsonify(self.data.getData(contentType='Folder')),
        )

    def test_filter_keys(self):
        jsonList = [
            {'@id': 'skdjf'},
            {'path': 'test'},
            {'key': 'Null'},
            {'key': 'Field NA'},
            {},
            {},
            {},
            {},
            {},
        ]

        self.pipeline.filter_keys(jsonList, excluded=['@id'])
        self.assertEqual(
            [
                {},
                {'path': 'test'},
                {},
                {},
                {},
                {},
                {},
                {},
                {},
            ],
            jsonList,
        )

    def test_fillblobintojson(self):
        # request files
        file_ = self.request.get('file')

        # files are at self.files
        self.view.files = {}
        self.view.requestFile(file_)

        # file structure and analyser
        self.files = utils.fileAnalyse(self.view.files)

        # convert csv to json
        data = self.pipeline.converttojson(data=self.files.getCsv(), header=[])

        for index in range(len(data)):

            obj_data = data[index]
            obj_data, temp_log = self.pipeline.fillblobintojson(
                obj_data,
                self.files.getFiles(),
                self.mapping,
            )
            if fnmatch.fnmatch(temp_log, ('*' + 'Error' + '*')):
                self.fail()
