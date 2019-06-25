from plone.importexport import _
from plone.importexport import utils

from plone.directives import form
from plone.app.z3cform.widget import QueryStringFieldWidget
from zope.component import queryMultiAdapter
from plone.restapi.interfaces import ISerializeToJson

from importexport import ImportExportView
from Products.Five import BrowserView

from zope import schema
from z3c.form import button
from plone.app.querystring.querybuilder import QueryBuilder
import os

import base64

class IExportForm(form.Schema):

    query = schema.List(
        title=_(u'Export'),
        description=_(u'Export contents from site'),
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False,
        missing_value=''
    )
    
    form.widget('query', QueryStringFieldWidget)

    limit = schema.Int(
        title=_(u'Limit'),
        description=_(u'Limit Search Results'),
        required=False,
        default=1000,
        min=1,
    )

    sort_on = schema.TextLine(
        title=_(u'label_sort_on', default=u'Sort on'),
        description=_(u'Sort the results'),
        required=False,
    )

    sort_reversed = schema.Bool(
        title=_(u'label_sort_reversed', default=u'Reversed order'),
        description=_(u'Sort the results in reversed order'),
        required=False,
    )

class ExportForm(form.SchemaForm):
    """ Define Form handling
    This form can be accessed as http://localhost:8080/@@export-form
    """

    schema = IExportForm
    ignoreContext = True

    def serialize(self, obj):
        data, errorLog = {}, ''
        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        try:
            data = serializer()
            self.views.exclude_attributes(data)
            data['path'] = os.path.join(*obj.getPhysicalPath())
        except Exception as e:
            path = obj.absolute_url_path()[1:]
            errorLog = str('Error: {} for {}\n'.format(repr(e), path))
        return data, errorLog
        
    @button.buttonAndHandler(u'Export')
    def handleExport(self, action):
        results = []
        data, errors = self.extractData()
        self.query = data['query']
        query_builder = QueryBuilder(self.context, self.request)
        listings = query_builder(self.query)

        self.views = ImportExportView(self.context, self.request)
        errorLogs = ''
        for listing in listings:
            obj = listing.getObject()
            result, errorLog = self.serialize(obj)
            if errorLog:
                import pdb; pdb.set_trace()
                errorLogs += errorLog
            else:
                results.append(result)
        self.zip = utils.InMemoryZip()
        self.conversion = utils.Pipeline()
        headers = ['@type']

        self.conversion.convertjson2(self, results, headers)
        self.request.response.setHeader('content-type', 'application/zip')
        id_ = self.context.absolute_url_path()[1:]
        cd = 'attachment; filename={}.zip'.format(id_)
        self.request.response.setHeader('Content-Disposition', cd)
        if errors:
            self.status = self.formErrorsMessage
            return
        self.status = 'Done!'
        self.content = self.zip.read()

        self.request.response.setBody(base64.b64encode(self.content), lock=True)
        # zip file is properly constructed here, uncomment the below lines to
        # save it locally
        # import pdb; pdb.set_trace()
        # tempfile = open('temp.zip', 'w+')
        # tempfile.write(self.content)
        # tempfile.close()
        return self.content
