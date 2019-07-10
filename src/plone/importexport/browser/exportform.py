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

from plone.importexport.browser.importexport import ImportExportView
from plone.importexport.exceptions import ImportExportError
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import directlyProvides

from plone.memoize import forever

@forever.memoize
def getHeaders(context, sort_headers=True):
    """
    Obtains headers required for exporting metadata
    """
    views = ImportExportView(context, context.REQUEST)
    try:
        headers = views.getheaders()
        # Sorting the metadata while displaying on the portal
        # aids the user to "quickly" find the metadata he is looking
        # for from the complete list
        if sort_headers:
            headers = sorted(headers)
        return headers
    except:
        ImportExportError('Error in retrieving headers')

def createSimpleTerm(pair):
    """
    Create zope.schema term out of the given pair.
    Supports creation of term in case pair is not a tuple by
    keeping the same value for `value`, `token` and `title`.
    """
    if not isinstance(pair, list):
        pair = [pair, pair, pair]
    term = SimpleTerm(value=pair[0], token=pair[0], title=pair[1])
    return term

def createTerms(items):
    """
    Create zope.schema terms for vocab from tuples (or list)
    """
    terms = [createSimpleTerm(pair) for pair in items]
    return terms

def metadataChoices(context):
    """
    Builds dynamic vocabulary for serving metadata in multi-valued
    field on export frontend
    """
    headers = getHeaders(context)
    terms = createTerms(headers)
    return SimpleVocabulary(terms)

# Interfacing metadataChoices with IContextSourceBinder for dynamic vocabularies
directlyProvides(metadataChoices, IContextSourceBinder)

class IExportForm(form.Schema):
    """
    Define schema for ExportForm
    """

    query = schema.List(
        title=_(u'Export'),
        description=_(u'Export contents from site (Import functionality to be added)'),
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False,
        missing_value=''
    )

    form.widget('query', QueryStringFieldWidget)

    form.mode(sort_on='hidden')
    sort_on = schema.TextLine(required=False)

    # Note: Metadata is not fixed and hence we just cannot directly
    # hardcode it in a list. Hence dynamic vocabulary is used here
    # to extract all the headers from the context (and request) object.

    # Using schema.list with schema.choice will can provide the option for
    # multi valued field
    metadata = schema.List(title=u'Metadata',
                          required=False,
                          value_type=schema.Choice(source=metadataChoices)
    )

    exclude_metadata = schema.Bool(
        title=_(u'Exclude selected metadata'),
        required=True,
        default=False
    )

    preserve_path = schema.Choice(
        title=_(u'Preserve relative path'),
        required=True,
        vocabulary=SimpleVocabulary(createTerms(['True', 'False']))
    )

    export_format = schema.Choice(
        title=_(u'Format for performing export'),
        required=True,
        vocabulary=SimpleVocabulary(createTerms(['csv', 'files', 'combined']))
    )

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
        Attaches an export handler button to the ExportForm
        """

        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        return self.baseExport(data)

    def baseExport(self, data):
        """
        Main base function for handling export functionality
        """

        results, errorLogs = [], ''

        # NOTE: The data that we obtain using the QueryStringFieldWidget
        # is only a json object which contains "what" query was performed
        # However, here we need the "results" of what query was performed
        # The core functionality of QueryStringFieldWidget is handled by
        # QueryBuilder, which provides a listing (or batch depending on
        # whether we set batch=True). This listing contains all the objects
        # that matches the given query and can be used for the export operation
        self.query = data['query']

        self.sort_on = data['sort_on']

        query_builder = QueryBuilder(self.context, self.request)
        listings = query_builder(self.query, sort_on=self.sort_on)

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
        self.headers = data['metadata']
        self.exclude_metadata = data['exclude_metadata']
        self.preserve_path = (data['preserve_path'] == 'True')

        # Setting the value in self.request as it is required in convertjson
        # function in utils.Pipeline
        self.request.set('exportFormat', data['export_format'])

        # If no metadata is selected, then by default export
        # all the metadata
        if not len(self.headers):
            self.headers = getHeaders(self.context)

        # Adding functionality to let user select which all functionalities he
        # wishes to exclude (instead of include)
        # Useful when we want limited headers to be not present in the metadata
        if self.exclude_metadata:
            self.headers = sorted(list(set(getHeaders(self.context)) - set(self.headers)))

        self.conversion.convertjson(self, results, self.headers, self.preserve_path)

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

    @button.buttonAndHandler(u'Reset')
    def handleReset(self, action):
        """
        Attaches a reset button to the ExportForm
        This provides a functionality to reset the selection made in the export form
        """
        self.request.response.redirect(self.request.URL)

    @button.buttonAndHandler(u'Export all')
    def handleExportAll(self, action):
        """
        Attaches an "export all" button to the ExportForm
        This provides a functionality to export all the content from the site
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # The below query allows us to obtain all the data present in the site
        data['query'] = [{u'i': u'Title', u'o': u'plone.app.querystring.operation.string.contains', u'v': u''}]
        return self.baseExport(data)
