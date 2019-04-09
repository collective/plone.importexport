from plone.directives import form
from zope import schema

from plone.importexport import _


class IImportExportSettings(form.Schema):
    metadatafields_as_primary_keys = schema.List(
        title=_(u'Metadata fields that should be used as primary keys'),
        description=_(
            u'help_metadatafields_as_primary_keys',
            default=_(u'The selected metadata fields will be shown as the '
                      u'possible primary key to import or update content ')),
        required=False,
        default=[
            u'path',
            u'UID'
        ],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary='plone.app.contenttypes.metadatafields'
        ),
    )
