import json
# An Adapter to serialize a Dexterity object into a JSON object.
from plone.restapi.interfaces import ISerializeToJson
# An adapter to deserialize a JSON object into an object in Plone.
from plone.restapi.interfaces import IDeserializeFromJson
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryMultiAdapter
from zExceptions import BadRequest
import zope
import UserDict
from plone.restapi.exceptions import DeserializationError
from zope.publisher.interfaces.browser import IBrowserRequest
from DateTime import DateTime
from random import randint
from urlparse import urlparse
import fnmatch
from plone.importexport import utils
import os
from plone.importexport.exceptions import ImportExportError
from plone import api
from plone.api.exc import MissingParameterError
from plone.api.exc import InvalidParameterError
from Products.CMFPlone.resources import add_resource_on_request

global MUST_EXCLUDED_ATTRIBUTES
global MUST_INCLUDED_ATTRIBUTES
# global files

# files = {}
# global uploadedfile
#
# uploadedfile = 'test'


# these attributes must be excluded while exporting
MUST_EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id',
                       'scales', 'items_total', 'table_of_contents', ]

# these attributes must be included while importing
MUST_INCLUDED_ATTRIBUTES = ['@type', 'path', 'id', 'UID']

class ImportExportView(BrowserView):
    """Import/Export page."""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.exportHeaders = None
        self.importHeaders = None
        self.existingPath = []
        self.files = {}
        # self.uploadedfile = 'None'
        # print "initiated"

    # this will del MUST_EXCLUDED_ATTRIBUTES from data till leaves of the tree
    def exclude_attributes(self, data=None):
        if not data:
            raise ImportExportError('Provide Data')

        if isinstance(data, dict):
            for key in data.keys():

                if key in MUST_EXCLUDED_ATTRIBUTES:
                    del data[key]
                    continue

                if isinstance(data[key], dict):
                    self.exclude_attributes(data[key])
                elif isinstance(data[key], list):
                    for index in range(len(data[key])):
                        self.exclude_attributes(data[key][index])

    def serialize(self, obj=None):

        if not obj:
            raise ImportExportError('Object required to serialize')

        results = []
        # using plone.restapi to serialize
        try:
            serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        except:
            raise ImportExportError("Error while quering adapter for serializer")

        if not serializer:
            raise ImportExportError('Cannot find any adapter for serializer')

        data = serializer()

        # del MUST_EXCLUDED_ATTRIBUTES from data
        self.exclude_attributes(data)

        data['path'] = str(obj.absolute_url_path()[1:])

        # record required data
        if data.get('@type', None) != "Plone Site":
            results = [data]

        for member in obj.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type != "Plone Site":
                try:
                    results += self.serialize(member)
                except ImportExportError as e:
                    error = e.message + ' for ' + data['path']
                    raise ImportExportError(error)
                except :
                    error = 'Fatal Error for ' + data['path']
                    raise ImportExportError(error)
        return results

    # context == requested object, data=metadata for object in json string
    # existing content are identified by path and ignored if requested
    def deserialize(self, context=None, data=None):

        if not context or not data:
            raise ImportExportError('Provide 2 good attributes')

        path = str(context.absolute_url_path()[1:])

        if self.request.get('actionExist', None)=='ignore' and (path in self.existingPath):
            return 'Ignoring existing content at {} \n'.format(path)


        # deserializing review_state
        new_state = None
        if data.get('review_state', None):
            new_state = str(data['review_state'])

        # restapi expects a string of JSON data
        data = json.dumps(data)

        '''creating a spoof request with data embeded in BODY attribute,
            as expected by restapi'''
        request = UserDict.UserDict(BODY=data)

        # binding request to BrowserRequest
        zope.interface.directlyProvides(request, IBrowserRequest)

        # using plone.restapi to deserialize
        try:
            deserializer = queryMultiAdapter((context, request),
                                         IDeserializeFromJson)
        except:
            raise ImportExportError("Error while quering adapter")

        try:
            deserializer()
            if new_state:
                state = str(api.content.get_state(obj=context, default=None))
                if new_state!=state:
                    api.content.transition(obj=context, to_state=new_state)

            return "Success for {} \n".format(path)
        except MissingParameterError as e:
            raise ImportExportError('parameter is missing for review_state')
        except InvalidParameterError as e:
            raise ImportExportError('Invalid parameter for review_state')
        except DeserializationError as e:
            error = str(str(e.message) + ' for '+ path + '\n')
        except BadRequest as e:
            error = str(str(e.message) + ' for '+ path + '\n')
        except ValueError as e:
            error = str(str(e.message) + ' for '+ path + '\n')
        except:
            error = str('Fatal Error for '+ path + '\n')
        return error

    def export(self):

        global MUST_INCLUDED_ATTRIBUTES
        errors = []
        try:
            # create zip in memory
            self.zip = utils.InMemoryZip()

            # defines Pipeline
            self.conversion = utils.Pipeline()

            if self.request and self.request.method == 'POST':

                # get id_ of Plone sites
                id_ = self.context.absolute_url_path()[1:]

                exportType = self.request.get('exportFormat', None)

                if self.request.get('exportFields', None) and (exportType=='csv' or exportType=='combined'):

                    # fields/keys to include
                    include = self.request.get('exportFields', None)
                    # BUG in html checkbox input, which send value as a string if only one value have been checked
                    if isinstance(include, str):
                        include = [include]
                    include = list(set(MUST_INCLUDED_ATTRIBUTES +
                        include))

                else:
                    # 'No check provided. Thus exporting whole content'
                    include = self.getheaders()
                    include = list(set(MUST_INCLUDED_ATTRIBUTES +
                        include))

                # results is a list of dicts
                try:
                    results = self.serialize(self.context)
                except ImportExportError as e:
                    raise ImportExportError(e.message)
                except:
                    raise ImportExportError('Error while serializing')
                try:
                    self.conversion.convertjson(self, results, include)
                except ImportExportError as e:
                    raise ImportExportError(e.message)
                except:
                    raise ImportExportError('Error in the Pipeline')


                self.request.RESPONSE.setHeader('content-type', 'application/zip')
                cd = 'attachment; filename=%s.zip' % (id_)
                self.request.RESPONSE.setHeader('Content-Disposition', cd)

                return self.zip.read()
            else:
                raise ImportExportError('Invalid Request')
        except ImportExportError as e:
            errors.append(e.message)
        except:
            errors.append('Invalid request')

        return errors

    # invoke non-existent content,  if any
    def createcontent(self, data=None):

        if not data:
            raise ImportExportError('Bad Request')

        log = ''
        for index in range(len(data)):

            obj_data = data[index]

            if not obj_data.get('path', None):
                log += 'pathError in {}\n'.format(obj_data['path'])
                continue

            #  os.sep is preferrable to support multiple filesystem
            #  return parent of context
            try:
                obj = self.getobjcontext(
                    obj_data['path'].split(os.sep)[:-1])
            except ImportExportError as e:
                log += e.message + 'for {}\n'.format(
                    obj_data['path'])
                continue

            if not obj:
                log += 'Parent object not found for {}\n'.format(
                    obj_data['path'])
                continue

            id_ = obj_data.get('id', None)
            title = obj_data.get('title', None)

            # creating  random id
            if not id_:
                now = DateTime()
                new_id = '{}.{}.{}{:04d}'.format(
                    type_.lower().replace(' ', '_'),
                    now.strftime('%Y-%m-%d'),
                    str(now.millis())[7:],
                    randint(0, 9999))
                if not title:
                    title = new_id
            else:
                new_id = id_

            # check if context exist
            if not obj.get(new_id, None):

                    log += 'creating new object {}\n'.format(
                        obj_data['path'].split(os.sep)[-1])

                    if not obj_data.get('@type', None):
                        log += 'typeError in {}\n'.format(obj_data['path'])
                        continue
                    type_ = obj_data.get('@type', None)

                    # Create object
                    try:
                        ''' invokeFactory() is more generic, it can be used for
                        any type of content, not just Dexterity content and it
                        creates a new object at
                        http://localhost:8080/self.context/new_id '''

                        new_id = obj.invokeFactory(type_, new_id, title=title)
                    except BadRequest as e:
                        # self.request.response.setStatus(400)
                        log += 'BadRequest {}\n'.format(str(e.message))
                    except ValueError as e:
                        # self.request.response.setStatus(400)
                        log += 'ValueError {}\n'.format(str(e.message))

        return log

    # get list of existingPath
    def getExistingpath(self, context=None):

        if not context:
            context = self.context
            self.existingPath = []

        if context.portal_type != "Plone Site":
            self.existingPath.append(str(context.absolute_url_path()[1:]))
            # self.existingPath.append(str(context))

        for member in context.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type != "Plone Site":
                    self.getExistingpath(member)

    #  provide list of path that occured in Plone server and uploaded csv
    def getCommanpath(self, dataPath=None):

        if not dataPath:
            raise ImportExportError('Provide dataPath to compare')

        comman = []

        # get list of existingPath
        self.getExistingpath()

        for path in dataPath:
            if path in self.existingPath:
                comman.append(path)

        return comman

    # if creating new content against existing content
    def getCommancontent(self):

        # TODO get uploaded csv_file from advanced tab onClick
        if not self.files:
            return

        csv_file = self.files.getCsv()

        # get path form csv_file
        conversion = utils.Pipeline()
        jsonList = conversion.converttojson(data=csv_file, header=['path'])

        for element in jsonList:
            path_.append(element.get('path', None))

        comman_path = self.getCommanpath(path_)

        return comman_path

    # requires path list from root
    def getobjcontext(self, path):

        try:
            obj = self.context
        except:
            raise ImportExportError('Bad Request')

        # FIXME raise error in log_file if element not present in site,

        # traversing to the desired folder
        for element in path[1:]:
            try:
                obj = obj[element]
            except:
                return None

        return obj

    def requestFile(self, file_=None):
        if not file_ :
            raise ImportExportError("Provide File")

        if isinstance(file_, list):
            for element in file_:
                    self.requestFile(element)

        else:
            file_.seek(0)
            if not file_.read():
                raise ImportExportError("Provide File")
            type_ =  file_.headers.values()[0].split('/')[-1]
            file_.seek(0)
            filename =  file_.filename
            # analyse = utils.fileAnalyse()
            # type_ = analyse.getFiletype(file_)

            self.files[filename] = {"file":file_ ,"type": type_, 'name':filename}
            return True

    def imports(self):

        global MUST_EXCLUDED_ATTRIBUTES
        global MUST_INCLUDED_ATTRIBUTES
        # global files

        try:
            if self.request.method == 'POST':

                # request files
                file_ = self.request.get('file')
                # files are at self.files
                self.requestFile(file_)

                # file structure and analyser
                self.files = utils.fileAnalyse(self.files)

                if not self.files.getCsv():
                    raise ImportExportError('Provide a good csv file')

                # create zip in memory
                self.zip = utils.InMemoryZip()

                # defines Pipeline
                self.conversion = utils.Pipeline()

                # defines mapping for UID
                self.mapping = utils.mapping(self)

                # get list of existingPath
                self.getExistingpath()

                error_log = ''
                temp_log = ''

                # check for include attributes in advanced tab
                if self.request.get('importFields', None):

                    # fields/keys to include
                    include = self.request.get('importFields', None)
                    # BUG in html checkbox input, which send value as a
                    #  string if only one value have been checked
                    if isinstance(include, str):
                        include = [include]
                    include = list(set(MUST_INCLUDED_ATTRIBUTES +
                        include))

                else:
                    # 'No check provided. Thus exporting whole content'
                    include = None

                # convert csv to json
                data = self.conversion.converttojson(self.files.getCsv(),
                 header=include)
                # invoke non-existent content,  if any
                error_log += self.createcontent(data)

                # map old and new UID in memory
                self.mapping.mapNewUID(data)

                # deserialize
                for index in range(len(data)):

                    obj_data = data[index]

                    if not obj_data.get('path', None):
                        error_log += 'pathError in {} \n'.format(obj_data['path'])
                        continue

                    # get blob content into json data
                    obj_data, temp_log = self.conversion.fillblobintojson(
                    obj_data, self.files.getFiles(), self.mapping)

                    error_log += temp_log

                    #  os.sep is preferrable to support multiple filesystem
                    #  return context of object
                    object_context = self.getobjcontext(
                        obj_data['path'].split(os.sep))

                    # all import error will be logged back
                    if object_context:
                        error_log += self.deserialize(object_context, obj_data)
                    else:
                        error_log += 'pathError for {}\n'.format(obj_data['path'])


                self.files = {}
                # self.request.RESPONSE.setHeader('content-type','application/text; charset=utf-8')
                print error_log

            else:
                raise ImportExportError('Invalid Request Method')

        except ImportExportError as e:
            self.files = {}
            return e.message
        except:
            self.files = {}
            return 'Bad Request'

    # return headers of serialized self.context
    def getheaders(self):

        if self.exportHeaders:
            return self.exportHeaders

        global MUST_EXCLUDED_ATTRIBUTES

        try:
            data = self.serialize(self.context)
        except ImportExportError as e:
            print e.message
            raise
        except:
            print 'Error while serializing'
            raise

        if not data:
            raise ImportExportError('Provide Data')

        try:
            conversion = utils.Pipeline()
            head = conversion.getcsvheaders(data)
        except ImportExportError as e:
            raise ImportExportError(e.message)
        except:
            raise ImportExportError('Fatal error while getting headers')


        self.exportHeaders = filter(lambda head: head not in MUST_INCLUDED_ATTRIBUTES,
            head)

        return self.exportHeaders

    # return matrix of headers
    def getmatrix(self, headers=None, columns=4):
        if not headers:
            raise ImportExportError('Provide Headers')

        matrix = {}
        count = len(headers)
        rows = float(count/columns)

        if isinstance(rows, float):
            rows = int(rows) + 1

        for index in range(rows):
            if count<1:
                continue
            matrix[index] = []
            for i in range(columns):
                if count<1:
                    continue
                count -= 1
                matrix[index].append(headers[count])

        return matrix

    # returns matrix of headers for self.context
    def getExportfields(self):

        try:
            # get headers of self.context
            headers = self.getheaders()
            # in matrix form
            matrix = self.getmatrix(headers=headers, columns=4)
        except ImportExportError as e:
            print (e.message)
            raise
        except:
            print ('Fatal error in fetching headers')
            raise

        return matrix

    # returns headers of imported csv file
    def getImportfields(self, importfile=None):

        global MUST_INCLUDED_ATTRIBUTES
        # TODO need to implement mechanism to get uploaded file
        # temp csv_file
        # csv_file = 'P2.csv'
        # csvData = open(csv_file,'r')

        now = DateTime()
        new_id = ''.format(randint(0, 9))
        csvData = str(new_id)
        csvData += 'fieldA, fieldB \n A,'

        try:
            # convert csv to json
            conversion = utils.Pipeline()
            jsonData = conversion.converttojson(data=csvData)
            # get headers from jsonData
            headers = conversion.getcsvheaders(jsonData)
        except ImportExportError as e:
            print e.message
            raise
        except:
            print ('Fatal error while converting csvData to jsonData')
            raise

        headers = filter(lambda headers: headers not in MUST_INCLUDED_ATTRIBUTES,
            headers)

        # get matrix of headers
        try:
            matrix = self.getmatrix(headers=headers, columns=4)
        except ImportExportError as e:
            print (e.message)
            raise
        except:
            print ('Fatal error in fetching headers')
            raise

        return matrix
