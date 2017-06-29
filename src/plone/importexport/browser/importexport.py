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

# TODO: in advanced tab, allow user to change this
EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id',
                       'scales', 'items_total', 'table_of_contents', ]


class ImportExportView(BrowserView):

    """Import/Export page."""
    template = ViewPageTemplateFile('importexport.pt')

    # del EXCLUDED_ATTRIBUTES from data
    def exclude_attributes(self, data):
        if isinstance(data, dict):
            for key in data.keys():
                if key in EXCLUDED_ATTRIBUTES:
                    del data[key]
                    continue
                if isinstance(data[key], dict):
                    self.exclude_attributes(data[key])
                elif isinstance(data[key], list):
                    # pdb.set_trace()
                    for index in range(len(data[key])):
                        self.exclude_attributes(data[key][index])

    def serialize(self, obj, path_):

        results = []
        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        if not serializer:
            return []
        data = serializer()

        # store paths of child object items
        if 'items' in data.keys():
            path = []
            for id_ in data['items']:
                url_path = urlparse(id_['@id']).path
                if url_path.startswith('/'):
                    # restapi path> /Plone/folder while zipfile> Plone/folder
                    url_path = url_path[1:]
                path.append(url_path)

        # del EXCLUDED_ATTRIBUTES from data
        self.exclude_attributes(data)

        data['path'] = path_
        if data['@type'] != "Plone Site":
            results = [data]
        for member in obj.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type != "Plone Site":
                results += self.serialize(member, path[0])
                del path[0]
        # pdb.set_trace()
        return results

    # self==parent of obj, obj== working context, data=metadata for context
    def deserialize(self, obj, data):
        # pdb.set_trace()

        id_ = data.get('id', None)
        type_ = data.get('@type', None)
        title = data.get('title', None)
        path = data.get('path', None)

        if not type_:
            return "Property '@type' is required. {} \n".format(path)

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
        if new_id not in obj.keys():
            print 'creating new object'
            # Create object
            try:
                ''' invokeFactory() is more generic, it can be used for any
                type of content, not just Dexterity content and it creates a
                new object at http://localhost:8080/self.context/new_id '''

                new_id = obj.invokeFactory(type_, new_id, title=title)
            except BadRequest as e:
                # self.request.response.setStatus(400)
                return 'DeserializationError {}'.format(str(e.message))
            except ValueError as e:
                # self.request.response.setStatus(400)
                return 'DeserializationError {}'.format(str(e.message))

        # restapi expects a string of JSON data
        data = json.dumps(data)
        '''creating a spoof request with data embeded in BODY attribute, as
           expected by restapi'''
        request = UserDict.UserDict(BODY=data)
        # binding request to BrowserRequest
        zope.interface.directlyProvides(request, IBrowserRequest)

        # context must be the parent request object
        context = obj[new_id]

        deserializer = queryMultiAdapter((context, request),
                                         IDeserializeFromJson)
        try:
            deserializer()
            # self.request.response.setStatus(201)
            return "Success for {} \n".format(path)
        except DeserializationError as e:
            # self.request.response.setStatus(400)
            # pdb.set_trace()
            return "DeserializationError {0} {1} \n".format(str(e), path)
        except:
            # pdb.set_trace()
            return "DeserializationError {0} {1} \n".format(str('e'), path)

    def export(self):

        # create zip in memory
        self.zip = utils.InMemoryZip()

        # defines Pipeline
        self.conversion = utils.Pipeline()

        if self.request.method == 'POST':

            # get id_ of Plone sites
            url = self.request.URL
            id_ = urlparse(url).path.split('/')[1]

            # pdb.set_trace()
            # results is a list of dicts
            results = self.serialize(self.context, id_)

            self.conversion.convertjson(self, results)

            self.request.RESPONSE.setHeader('content-type', 'application/zip')
            cd = 'attachment; filename=%s.zip' % (id_)
            self.request.RESPONSE.setHeader('Content-Disposition', cd)

            return self.zip.read()

        return

    # requires path list from root
    def getobjcontext(self, path):
        obj = self.context

        # FIXME raise error in log_file if element not present in site,
        # traversing to the desired folder
        for element in path[1:]:
            try:
                obj = obj[element]
            except:
                # TODO raise good error
                return None

        return obj

    def imports(self):

        # create zip in memory
        self.zip = utils.InMemoryZip()

        # defines Pipeline
        self.conversion = utils.Pipeline()

        # defines mapping for UID
        self.mapping = utils.mapping(self)

        error_log = ''

        # get file from form
        zip_file = self.request.get('importfile', None)

        if zip_file is None:
            error_log += 'No file provided'

        # TODO validate zip_file,files,csv_file
        if self.request.method == 'POST' and zip_file is not None:

            # pdb.set_trace()
            # unzip zip file
            files = self.zip.getfiles(zip_file)

            if not files:
                error_log += 'Please provide a good zip file'

            # get name of csv file
            for key in files.keys():
                if fnmatch.fnmatch(key, '*/*'):
                    pass
                elif fnmatch.fnmatch(key, '*.csv'):
                    csv_file = key

            # convert csv to json
            data = self.conversion.converttojson(files[csv_file])

            # filter out undefined keys
            self.conversion.filter(data)

            # get mapping of old and new UID
            self.map_UID = self.mapping.mapNewUID(data)
            # pdb.set_trace()

            # deserialize
            for index in range(len(data)):

                obj_data = data[index]

                # TODO raise the error into log_file
                if not obj_data['path']:
                    raise BadRequest("Property 'path' is required")

                # pdb.set_trace()

                # FIXME: solution for more than one image/file in an object
                if obj_data.get('image', None):
                    value = obj_data['image'].get('download', None)
                    if value and files.get(value, None):
                        try:
                            content = files[value].read()
                            obj_data['image']['data'] = content.encode(
                                                        "base64")
                            obj_data['image']['encoding'] = "base64"
                        except:
                            error_log += ('''Error in fetching/encoding blob
                            from zip {}'''.format(obj_data['path']))

                if obj_data.get('file', None):
                    # pdb.set_trace()
                    value = obj_data['file'].get('download', None)
                    if value and files.get(value, None):
                        try:
                            content = filess[value].read()
                            obj_data['file']['data'] = content.encode("base64")
                            obj_data['file']['encoding'] = "base64"
                        except:
                            error_log += ('''Error in fetching/encoding blob
                            from zip {}'''.format(obj_data['path']))

                if (obj_data.get('text', None) and
                        obj_data['text'].get('content-type', None)):
                    type_ = obj_data['text']['content-type'].split('/')[-1]
                    value = obj_data['text'].get('download', None)
                    if type_ == "html" and value and files.get(value, None):
                        try:
                            # pdb.set_trace()
                            file_data = files[value].read().decode(
                                obj_data['text']['encoding'])

                            # mapping old_UID with new_uid
                            file_data = self.mapping.internallink(
                                file_data).encode(obj_data['text']['encoding'])

                            obj_data['text']['data'] = file_data

                            del obj_data['text']['download']
                        except:
                            error_log += ('''Error in fetching/encoding blob
                            from zip {}'''.format(obj_data['path']))

                #  os.sep is preferrable to support multiple filesystem
                #  return parent of context
                parent_context = self.getobjcontext(
                    obj_data['path'].split(os.sep)[:-1])

                # all import error will be logged back
                error_log += self.deserialize(parent_context, obj_data)

        self.request.RESPONSE.setHeader(
            'content-type', 'application/text; charset=utf-8')
        return error_log

    def __call__(self):
        return self.template()
