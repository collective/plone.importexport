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
import csv
import cStringIO

# TODO: need commments upon these attributes
EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id', 'UID']


class ImportExportView(BrowserView):
    """Import/Export page."""

    template = ViewPageTemplateFile('importexport.pt')

    def serialize(self, obj, path_):
        # pdb.set_trace()

        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)
        if not serializer:
            return []
        data = serializer()

        # store paths of child object items
        if 'items' in data.keys():
            path = []
            for id_ in data['items']:
                path.append(urlparse(id_['@id']).path)

        for key in EXCLUDED_ATTRIBUTES:
            if key in data:
                del data[key]
        data['path'] = path_
        results = [data]
        for member in obj.objectValues():
            # TODO: defualt plone config @portal_type?
            if member.portal_type!="Plone Site":
                results += self.serialize(member,path[0])
                del path[0]
        return results

    # self==parent of obj, obj== working context, data=metadata for context
    def deserialize(self, obj, data):
        # pdb.set_trace()

        id_ = data.get('id', None)
        type_ = data.get('@type', None)
        title = data.get('title', None)

        if not type_:
            raise BadRequest("Property '@type' is required")


        # creating  random id
        if not id_:
            now = DateTime()
            new_id = '{}.{}.{}{:04d}'.format(
                type_.lower().replace(' ', '_'),
                now.strftime('%Y-%m-%d'),
                str(now.millis())[7:],
                randint(0, 9999))
        else:
            new_id = id_

        if not title:
            title = new_id

        # check if context exist
        if new_id not in obj.keys():
            print 'creating new object'
            # Create object
            try:
                ''' invokeFactory() is more generic, it can be used for any type of content, not just Dexterity content
                and it creates a new object at http://localhost:8080/self.context/new_id '''

                new_id = obj.invokeFactory(type_, new_id, title=title)
            except BadRequest as e:
                self.request.response.setStatus(400)
                return dict(error=dict(
                    type='DeserializationError',
                    message=str(e.message)))
            except ValueError as e:
                self.request.response.setStatus(400)
                return dict(error=dict(
                    type='DeserializationError',
                    message=str(e.message)))

        # restapi expects a string of JSON data
        data = json.dumps(data)
        # creating a spoof request with data embeded in BODY attribute, as expected by restapi
        request = UserDict.UserDict(BODY=data)
        # binding request to BrowserRequest
        zope.interface.directlyProvides(request, IBrowserRequest)

        # context must be the parent request object
        context = obj[new_id]

        deserializer = queryMultiAdapter((context, request), IDeserializeFromJson)
        if deserializer is None:
            self.request.response.setStatus(501)
            return dict(error=dict(
                message='Cannot deserialize type {}'.format(
                    obj.portal_type)))

        try:
            deserializer()
            self.request.response.setStatus(201)
            print 'deserializer works'
            # TODO: all error log should be returned to user
            return 'None'
        except DeserializationError as e:
            self.request.response.setStatus(400)
            return dict(error=dict(
                type='DeserializationError',
                message=str(e)))

    # return unique keys from list
    def getcsvheaders(self,data):
        header = []
        for dict_ in data:
            for key in dict_.keys():
                if key not in header:
                    header.append(key)

        return header

    def writejsontocsv(self,data_list):
        csv_output = cStringIO.StringIO()

        csv_headers =self.getcsvheaders(data_list)

        if not csv_headers:
            raise BadRequest("check json data, no keys found")

        try:
            '''The optional restval parameter specifies the value to be written if the dictionary is missing a key in fieldnames. If the dictionary passed to the writerow() method contains a key not found in fieldnames, the optional extrasaction parameter indicates what action to take. If it is set to 'raise' a ValueError is raised. If it is set to 'ignore', extra values in the dictionary are ignored.'''
            writer = csv.DictWriter(csv_output, fieldnames=csv_headers,restval='Field NA', extrasaction='raise', dialect='excel')
            writer.writeheader()
            for data in data_list:
                for key in data.keys():
                    if not data[key]:
                        data[key]="Null"
                    # TODO: store blob content and replace url with path
                    if isinstance(data[key],(dict,list)):
                        data[key] = json.dumps(data[key])
                writer.writerow(data)
        except IOError as (errno, strerror):
                print("I/O error({0}): {1}".format(errno, strerror))

        data =  csv_output.getvalue()
        csv_output.close()

        return data

    def export(self):
        # pdb.set_trace()
        if self.request.method == 'POST':

            # get home_path of Plone sites
            url = self.request.URL
            home_path = '/' + urlparse(url).path.split('/')[1]

            # results is a list of dicts
            results = self.serialize(self.context, home_path)

            csv_output = self.writejsontocsv(results)

            self.request.RESPONSE.setHeader(
                'content-type', 'application/csv; charset=utf-8')
            return csv_output
        return

    def getparentcontext(self,data):
        path_ = data['path'].split('/')

        obj = self.context

        # traversing to the desired folder
        for index in range(2,len(path_)-1):
            obj = obj[path_[index]]

        return obj

    def imports(self):
        # pdb.set_trace()
        if self.request.method == 'POST':


            # csv_file = '/home/shriyanshagro/Awesome_Stuff/Plone/zinstance/src/plone.importexport/src/plone/importexport/browser/export.csv'
            # json_data = self.readcsvasjson(csv_file)
            # TODO: implement a pipeline for converting CSV to JSON
            # TODO: implement mechanism for file upload
            data = {"path": "/Plone/GSoC17", "description": "Just GSoC stuff", "@type":"Folder",'title':"GSoC17"
            # "id": "newfolder"
            }

            if not data['path']:
                raise BadRequest("Property 'path' is required")

            # return parent of context
            parent_context = self.getparentcontext(data)

            # all import error will be logged back
            importerrors = self.deserialize(parent_context,data)

            self.request.RESPONSE.setHeader(
                'content-type', 'application/json; charset=utf-8')
            return json.dumps(importerrors)

        return

    def __call__(self):
        return self.template()
