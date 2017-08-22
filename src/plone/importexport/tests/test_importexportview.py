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

def compare_files(a,b):
    # create hash and compare
    fileA = hashlib.sha256(a.read()).digest()
    fileB = hashlib.sha256(b.read()).digest()
    if fileA == fileB:
        return True
    else:
        return False

class TestImportExportView(unittest.TestCase):
    """Test importexport view methods."""

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""

        # test zip file
        path = "../../src/plone/importexport/tests/Plone.zip"
        self.zip = open(path, 'r')
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['file'] = self.zip
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

    # def generateData(self):
    #     pass

    def test_import(self):

        # FIXME obj.invokeFactory throws Unauthorized Exception
        with api.env.adopt_roles(['Manager']):
            try:
                errors = self.view.imports()
            except Exception as e:
                self.fail(e)


    def test_export(self):

        try:
            # return a string of zip file
            export = self.view.export()
            # creating a file-like object
            export = StringIO(export)
        except Exception as e:
            self.fail(e)

        # Compare exported zip and test_import
        if not compare_files(export, self.zip):
            self.fail("import export files didn't match")


    # def test_serialize(self):
    #
    #     # XXX: Assign some object to obj
    #     obj = None
    #     # XXX: Assign valid path_
    #     path_ = ""
    #     results = self.view.serialize(obj, path_)
    #
    #     # XXX: Validate results
    #     ## self.assertIn('something', results)
    #
    #
    # def test_deserialize_error(self):
    #
    #     # XXX: Create an invalid data structure for importing
    #     data = {}
    #     results = self.view.deserialize(self.portal, data)
    #
    #     # XXX: Validate returned string
    #
    #     # XXX: Check objects not created
    #
    # def test_export(self):
    #     result = self.view.export()
    #
    #     # XXX: Validate exported result is a valid zip file with proper size

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
