
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.directives import form
from plone.registry.interfaces import IRegistry
from plone.z3cform import layout
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five.browser import BrowserView


from plone.importexport import _
from plone.importexport.interfaces import IImportExportSettings


class ImportExportSettingsForm(RegistryEditForm):
    """
    Import Export Settings
    """
    schema = IImportExportSettings
    schema_prefix = "importexport"
    label = (u"Import Export Settings")

    def getContent(self):
        try:
            data = super(ImportExportSettingsForm, self).getContent()
        except KeyError:
            data =  {
                'metadatafields_as_primary_keys': (u'path', u'UID')
            }
            registry = getUtility(IRegistry)
            registry.registerInterface(IImportExportSettings)
        return data


ImportExportSettingsFormView = layout.wrap_form(
   ImportExportSettingsForm, ControlPanelFormWrapper)


