# -*- coding: utf-8 -*-
import plone.importexport

from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from zope.configuration import xmlconfig


class PloneImportexportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        xmlconfig.file(
            'configure.zcml',
            plone.importexport,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.importexport:default')


PLONE_IMPORTEXPORT_FIXTURE = PloneImportexportLayer()


PLONE_IMPORTEXPORT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_IMPORTEXPORT_FIXTURE,),
    name='PloneImportexportLayer:IntegrationTesting'
)


PLONE_IMPORTEXPORT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_IMPORTEXPORT_FIXTURE,),
    name='PloneImportexportLayer:FunctionalTesting'
)


PLONE_IMPORTEXPORT_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONE_IMPORTEXPORT_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='PloneImportexportLayer:AcceptanceTesting'
)
