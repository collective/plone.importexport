import json
import pdb
# An Adapter to serialize a Dexterity object into a JSON object.
from plone.restapi.interfaces import ISerializeToJson
# An adapter to deserialize a JSON object into an object in Plone.
from plone.restapi.interfaces import IDeserializeFromJson
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryMultiAdapter
import zope
import UserDict
from plone.restapi.exceptions import DeserializationError
from zope.publisher.interfaces.browser import IBrowserRequest
from DateTime import DateTime
from random import randint

EXCLUDED_ATTRIBUTES = ['member', 'parent', ]


class ImportExportView(BrowserView):
    """Import/Export page."""

    template = ViewPageTemplateFile('importexport.pt')

    def serialize(self, obj):
        # pdb.set_trace()

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

    # self==parent of obj, obj== working context, data=metadata for context
    def deserialize(self, obj, data):
        pdb.set_trace()

        new_content = True
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
            # check if context exist
            for object_ in obj.items():
                if new_id == object_[0]:
                    new_content = False
                    break

        if not title:
            title = new_id

        # Create object
        if new_content:
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

    def export(self):
        # pdb.set_trace()
        if self.request.method == 'POST':
            results = self.serialize(self.context)

            self.request.RESPONSE.setHeader(
                'content-type', 'application/json; charset=utf-8')
            return json.dumps(results)
        return

    def getparentcontext(self,data):
        path_ = data['path'].split('/')

        obj = self.context

        # traversing to the desired folder
        for index in range(2,len(path_)-1):
            obj = obj[path_[index]]

        return obj

    def imports(self):
        pdb.set_trace()
        if self.request.method == 'POST':

            # TODO: implement a pipeline for converting CSV to JSON
            data = {"path": "/Plone/newfolder", "description": "some new folder", "@type":"Folder",
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
