# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.importexport.testing import PLONE_IMPORTEXPORT_INTEGRATION_TESTING  # noqa
from plone import api

import unittest2 as unittest
from zope.component import getMultiAdapter

EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id',
                       'scales', 'items_total', 'table_of_contents', ]

class TestImportExportView(unittest.TestCase):
    """Test importexport view methods."""

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.view = getMultiAdapter((self.portal, self.request), name="import-export")

    def test_template_renders(self):
        results = self.view()
        # XXX: Check some string from this template
        self.assertIn("Select a CSV or a ZIP file providing the contents to import.", results)

    def test_exclude_attributes(self):
        data = {
            'member': 1,
            'parent': 1,
            'items': 1,
            'changeNote': 1,
            '@id': 1,
            'scales': 1,
            'items_total': 1,
            'table_of_contents': 1
        }
        self.view.exclude_attributes(data)
        for key in EXCLUDED_ATTRIBUTES:
            # XXX: asertNotIn not present
            if key in data.keys():
                self.fail("%s key should not be present" % key)

    def test_serialize(self):

        # XXX: Assign some object to obj
        obj = None
        # XXX: Assign valid path_
        path_ = ""
        results = self.view.serialize(obj, path_)

        # XXX: Validate results
        ## self.assertIn('something', results)

    def test_deserialize(self):

        # XXX: Create a valid data structure for importing
        data = {}
        results = self.view.deserialize(self.portal, data)

        # XXX: Validate returned string

        # XXX: Check objects created

    def test_deserialize_error(self):

        # XXX: Create an invalid data structure for importing
        data = {}
        results = self.view.deserialize(self.portal, data)

        # XXX: Validate returned string

        # XXX: Check objects not created

    def test_export(self):
        result = self.view.export()

        # XXX: Validate exported result is a valid zip file with proper size
