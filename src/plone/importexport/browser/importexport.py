import json
import pdb
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

global MUST_EXCLUDED_ATTRIBUTES
global MUST_INCLUDED_ATTRIBUTES
global included_attributes
global excluded_attributes
global existing_content

# list of existing ids
existing_content = []

# these attributes must be excluded while exporting
MUST_EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id',
                       'scales', 'items_total', 'table_of_contents', ]

# these attributes must be included while importing
MUST_INCLUDED_ATTRIBUTES = ['@type', 'UID', 'path', 'id']

class ImportExportView(BrowserView):
    """Import/Export page."""

    # del excluded_attributes from data
    def exclude_attributes(self, data=None):
        if not data:
            raise ImportExportError('Provide Data')

        global excluded_attributes

        if isinstance(data, dict):
            for key in data.keys():
                if key in excluded_attributes:
                    del data[key]
                    continue
                if isinstance(data[key], dict):
                    self.exclude_attributes(data[key])
                elif isinstance(data[key], list):
                    # pdb.set_trace()
                    for index in range(len(data[key])):
                        self.exclude_attributes(data[key][index])

    # allow only included_attributes in data
    def include_attributes(self, data):
        global included_attributes
        # pdb.set_trace()
        if isinstance(data, dict):
            for key in data.keys():
                if key not in included_attributes:
                    del data[key]
                    continue

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

        # include/exclude checks
        if self.request.get('check', None):
            if self.request.check == 'exclude':
                # del excluded_attributes from data
                self.exclude_attributes(data)
            elif self.request.check == 'include':
                # include only included_attributes in data
                self.include_attributes(data)
        else:
            # del excluded_attributes from data
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

    def getheaders(self, data=None, columns=4):

        if not data:
            raise ImportExportError('Provide Data')

        global MUST_INCLUDED_ATTRIBUTES

        try:
            conversion = utils.Pipeline()
            head = conversion.getcsvheaders(data)
        except ImportExportError as e:
            raise ImportExportError(e.message)
        except:
            raise ImportExportError('Fatal error while getting headers')


        headers = filter(lambda head: head not in MUST_INCLUDED_ATTRIBUTES,
            head)

        matrix = {}
        # pdb.set_trace()

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

    # returns fields for context
    def getExportfields(self):

        global MUST_EXCLUDED_ATTRIBUTES
        global excluded_attributes

        excluded_attributes = MUST_EXCLUDED_ATTRIBUTES

        try:
            data = self.serialize(self.context)
        except ImportExportError as e:
            print e.message
            raise
        except:
            print 'Error while serializing'
            raise

        # in matrix form
        try:
            matrix = self.getheaders(data=data, columns=4)
        except ImportExportError as e:
            print (e.message)
            raise
        except:
            print ('Fatal error in fetching headers')
            raise

        return matrix

    # returns fields for csv file
    def getImportfields(self):

        # TODO need to implement mechanism to get uploaded file
        # temp csv_file
        csv_file = 'P2.csv'
        csvData = open(csv_file,'r')

        # convert csv to json
        try:
            conversion = utils.Pipeline()
            jsonData = conversion.converttojson(csvData)
        except ImportExportError as e:
            print e.message
            raise
        except:
            print ('Fatal error while converting csvData to jsonData')
            raise

        # get headers from json_jsonData
        try:
            matrix = self.getheaders(data=jsonData, columns=4)
        except ImportExportError as e:
            print (e.message)
            raise
        except:
            print ('Fatal error in fetching headers')
            raise

        return matrix

    # context == requested object, data=metadata for object in json string
    def deserialize(self, context=None, data=None):

        if not context or not data:
            raise ImportExportError('Provide 2 good attributes')

        global existing_content

        path = data.get('path')

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
            return "Success for {} \n".format(path)
        except DeserializationError as e:
            error = str(e.message + ' for '+ path + '\n')
        except BadRequest as e:
            error = str(e.message + ' for '+ path + '\n')
        except ValueError as e:
            error = str(e.message + ' for '+ path + '\n')
        except:
            error = str('Fatal Error for '+ path + '\n')
        return error

    def export(self):

        global MUST_EXCLUDED_ATTRIBUTES
        global MUST_INCLUDED_ATTRIBUTES
        global included_attributes
        global excluded_attributes
        errors = []

        try:
            # create zip in memory
            self.zip = utils.InMemoryZip()

            # defines Pipeline
            self.conversion = utils.Pipeline()

            if self.request and self.request.method == 'POST':

                # get id_ of Plone sites
                id_ = self.context.absolute_url_path()[1:]

                # pdb.set_trace()
                if self.request.get('check', None):
                    if self.request.check == 'exclude':
                        # fields/keys to exclude
                        exclude = self.request.excluded_attributes.split(',')
                        # FIXME matchcase, filter spaces and other unwanted characters

                        # get unique values in list
                        excluded_attributes = list(set(MUST_EXCLUDED_ATTRIBUTES + exclude))

                    elif self.request.check == 'include':
                        include = self.request.included_attributes.split(',')
                        # FIXME matchcase, filter spaces and other unwanted characters

                        # get unique values in list
                        included_attributes = list(set(include))
                else:
                    excluded_attributes = MUST_EXCLUDED_ATTRIBUTES
                    errorlog = 'No check provided. Thus exporting whole content'

                # results is a list of dicts
                try:
                    results = self.serialize(self.context)
                except ImportExportError as e:
                    raise ImportExportError(e.message)
                except:
                    raise ImportExportError('Error while serializing')

                try:
                    self.conversion.convertjson(self, results)
                except ImportExportError as e:
                    raise ImportExportError(e.message)
                except:
                    raise ImportExportError('Error in the Pipeline')


                self.request.RESPONSE.setHeader('content-type', 'application/zip')
                cd = 'attachment; filename=%s.zip' % (id_)
                self.request.RESPONSE.setHeader('Content-Disposition', cd)

                return self.zip.read()
            else:
                # pdb.set_trace()
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

        global existing_content

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

            elif self.request.get('action',None) and self.request.action == 'ignore':
                existing_content.append(new_id)

        return log

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

    def imports(self):

        global MUST_EXCLUDED_ATTRIBUTES
        global MUST_INCLUDED_ATTRIBUTES

        try:

            if self.request.method == 'POST':

                # create zip in memory
                self.zip = utils.InMemoryZip()

                # defines Pipeline
                self.conversion = utils.Pipeline()

                # defines mapping for UID
                self.mapping = utils.mapping(self)

                error_log = ''
                temp_log = ''

                # get file from form
                zip_file = self.request.get('importfile', None)

                # unzip zip file
                files = self.zip.getfiles(zip_file)

                # get name of csv file
                for key in files.keys():
                    if fnmatch.fnmatch(key, '*/*'):
                        pass
                    elif fnmatch.fnmatch(key, '*.csv'):
                        csv_file = key

                # convert csv to json
                data = self.conversion.converttojson(files[csv_file])

                attribute = []

                # check for include/exclude in advanced tab
                if self.request.get('check', None):
                    # pdb.set_trace()
                    if self.request.check == 'exclude':
                        # fields/keys to exclude
                        exclude = self.request.excluded_attributes.split(',')
                        # FIXME matchcase, filter spaces and other unwanted characters

                        # check to include MUST_INCLUDED_ATTRIBUTES in import file
                        attribute = filter(lambda x: x not in MUST_INCLUDED_ATTRIBUTES, exclude)

                        # filter out keys
                        self.conversion.filter_keys(data, attribute)

                    elif self.request.check == 'include':
                        include = self.request.included_attributes.split(',')
                        # FIXME matchcase, filter spaces and other unwanted characters

                        included_attributes = list(set(MUST_INCLUDED_ATTRIBUTES + include))

                        # include only certain keys
                        self.conversion.include_keys(data, included_attributes)

                else:
                    errorlog = 'No check provided. Thus importing whole content'
                    # filter out undefined keys
                    self.conversion.filter_keys(data, attribute)

                # invoke non-existent content,  if any
                error_log += self.createcontent(data)

                # map old and new UID in memory
                self.mapping.mapNewUID(data)

                # deserialize
                for index in range(len(data)):

                    # pdb.set_trace()
                    obj_data = data[index]

                    if not obj_data.get('path', None):
                        error_log += 'pathError in {} \n'.format(obj_data['path'])
                        continue

                    # check for actions in advance tab
                    if self.request.get('action', None) and self.request.action == 'ignore' and obj_data['id'] in existing_content:
                        error_log += 'Content for {0} already exist \n'.format(obj_data['path'])
                        continue

                    # get blob content into json data
                    obj_data, temp_log = self.conversion.fillblobintojson(
                    obj_data, files, self.mapping)
                    # pdb.set_trace()

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

                self.request.RESPONSE.setHeader(
                    'content-type', 'application/text; charset=utf-8')

                return error_log

            else:
                raise ImportExportError('Invalid Request Method')

        except ImportExportError as e:
            return e.message
        except:
            return 'Bad Request'
