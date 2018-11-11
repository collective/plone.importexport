# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.importexport.testing import PLONE_IMPORTEXPORT_INTEGRATION_TESTING

import unittest


class TestSetup(unittest.TestCase):
    """Test that plone.importexport is properly installed."""

    layer = PLONE_IMPORTEXPORT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if plone.importexport is installed
        with portal_quickinstaller."""
        self.assertTrue(
            self.installer.isProductInstalled('plone.importexport'),
        )

    def test_uninstall(self):
        """Test if plone.importexport is cleanly uninstalled."""
        self.installer.uninstallProducts(['plone.importexport'])
        self.assertFalse(
            self.installer.isProductInstalled('plone.importexport'),
        )
