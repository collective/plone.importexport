from plone.importexport import _
from plone.importexport import utils

from plone.directives import form
from plone.app.z3cform.widget import QueryStringFieldWidget
from zope.component import queryMultiAdapter
from plone.restapi.interfaces import ISerializeToJson

from importexport import exclude_attributes
from Products.Five import BrowserView

from zope import schema
from z3c.form import button
from plone.app.querystring.querybuilder import QueryBuilder
import os

class IExportForm(form.Schema):
    """
    Define schema for ExportForm
    """

    query = schema.List(
        title=_(u'Export'),
        description=_(u'Export contents from site'),
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False,
        missing_value=''
    )
    
    form.widget('query', QueryStringFieldWidget)

class ExportForm(form.SchemaForm):
    """
    Define form handling
    """

    schema = IExportForm
    ignoreContext = True

    def serialize(self, obj):
        """
        Serialize the given object to json
        """

        data, errorLog = {}, ''
        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        try:
            data = serializer()
            exclude_attributes(data)
        except Exception as e:
            path = obj.absolute_url_path()[1:]
            errorLog = str('Error: {} for {}\n'.format(repr(e), path))
        return data, errorLog

    @button.buttonAndHandler(u'Export')
    def handleExport(self, action):
        """
        Attach an export handler button to the ExportForm
        """

        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        results, errorLogs = [], ''

        # NOTE: The data that we obtain using the QueryStringFieldWidget
        # is only a json object which contains "what" query was performed
        # However, here we need the "results" of what query was performed
        # The core functionality of QueryStringFieldWidget is handled by
        # QueryBuilder, which provides a listing (or batch depending on
        # whether we set batch=True). This listing contains all the objects
        # that matches the given query and can be used for the export operation
        self.query = data['query']
        query_builder = QueryBuilder(self.context, self.request)
        listings = query_builder(self.query)

        for listing in listings:
            obj = listing.getObject()
            result, errorLog = self.serialize(obj)
            if errorLog:
                import pdb; pdb.set_trace()
                errorLogs += errorLog
            else:
                # Adding path to the data is a requirement for
                # utils.Pipeline.convertjson function
                result['path'] = os.path.join(*obj.getPhysicalPath())
                results.append(result)

        # NOTE: Using an in memory zip will crash in case of large zip files
        # TODO: Look for an alternate solution than having to build the
        # complete zip in memory. It would be a better approach
        # to stream the content on the fly (instead of continously appending
        # the content to a zip file)

        self.zip = utils.InMemoryZip()
        self.conversion = utils.Pipeline()
        headers = ['@type']

        self.conversion.convertjson(self, results, headers)

        # Dispatch the zip file from the browser
        self.request.response.setHeader('Content-Type', 'application/zip')
        id_ = self.context.absolute_url_path()[1:]
        cd = 'attachment; filename={}.zip'.format(id_)
        self.request.response.setHeader('Content-Disposition', cd)
        self.content = self.zip.read()

        self.status = 'Done!'

        # NOTE: Most of the resources that are available for
        # content-disposition uses .setBody() method
        # However, response.setBody() doesn't work here (it doesn't do the streaming)
        # and ultimately using .setBody results in a decoding error
        # Hence we use the .write method here, which directly streams the
        # content as it is on the browser, thereby preventing the decoding error
        self.request.response.write(self.content)