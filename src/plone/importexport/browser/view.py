import json

from plone.restapi.interfaces import ISerializeToJson
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryMultiAdapter

EXCLUDED_ATTRIBUTES = ['member', 'parent', ]


class ImportExportView(BrowserView):
    """Import/Export page."""

    template = ViewPageTemplateFile('importexport.pt')

    def serialize(self, obj):
        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        if not serializer:
            return []
        data = serializer()
        for key in EXCLUDED_ATTRIBUTES:
            if key in data:
                del data[key]
        results = [data]
        for member in obj.objectValues():
            results += self.serialize(member)
        return results

    def export(self):
        if self.request.method == 'POST':
            results = self.serialize(self.context)

            self.request.RESPONSE.setHeader(
                'content-type', 'application/json; charset=utf-8')
            return json.dumps(results)

    def __call__(self):
        return self.template()
