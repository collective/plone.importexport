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
import StringIO, cStringIO
import zipfile
import fnmatch
import operator

# TODO: in advanced tab, allow user to change this
EXCLUDED_ATTRIBUTES = ['member', 'parent', 'items', 'changeNote', '@id', 'UID', 'scales', 'items_total', 'table_of_contents', ]

class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0

        return self

    def read(self):
        '''Returns a string with the contents of the in-memory zip.'''
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def getfiles(self,zip_file):
        data = {}
        zfile = zipfile.ZipFile(zip_file,'r')
        for name in zfile.namelist():
            '''.open() returns a file-like object while .read() return a string like object
            And csv.DictWriter needs a file like object'''
            data[name] = zfile.open(name)
        return data

class Pipeline(object):
    # return unique keys from list
    def getcsvheaders(self,data):
        # HACK to keep these fields at first in csv
        header = {'@type':3,'path':2, 'id':1}
        for dict_ in data:
            for key in dict_.keys():
                if key not in header.keys():
                    header[key]=1
                else:
                    header[key] += 1

        result = []
        header = sorted(header.items(),key=operator.itemgetter(1), reverse=True)
        for key in header:
            result.append(key[0])
        # pdb.set_trace()
        return result

    def convertjson(self,obj,data_list):
        csv_output = cStringIO.StringIO()

        url = obj.request.URL
        id_ = urlparse(url).path.split('/')[1]

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
                    if isinstance(data[key],(dict,list)):

                        # store blob content and replace url with path
                        if isinstance(data[key],dict) and 'download' in data[key].keys():
                            # pdb.set_trace()

                            parse = urlparse(data[key]['download']).path.split('/')
                            file_path = '/'.join(parse[2:-2])

                            try:
                                if data[key]['content-type'].split('/')[0]=='image':
                                    file_data = obj.context.restrictedTraverse(str(file_path)+'/image').data
                                else:
                                    file_data = obj.context.restrictedTraverse(str(file_path)+'/file').data
                            except:
                                print 'Blob data fetching error'
                            else:
                                filename = data[key]['filename']
                                # pdb.set_trace()
                                data[key]['download'] = id_+'/'+file_path+'/'+filename
                                obj.zip.append(data[key]['download'],file_data)

                        # converting list and dict to quoted json
                        data[key] = json.dumps(data[key])
                writer.writerow(data)
        except IOError as (errno, strerror):
                print("I/O error({0}): {1}".format(errno, strerror))
        else:
            obj.zip.append(id_+'.csv',csv_output.getvalue())
            csv_output.close()


        return

    def converttojson(self,data):
        reader = csv.DictReader(data)
        data = []
        for row in reader:
            data.append(row)
        # jsonify quoted json values
        data = self.jsonify(data)
        return data

    # jsonify quoted json values
    def jsonify(self,data):
        if isinstance(data,dict):
            for key in data.keys():
                data[key] = self.jsonify(data[key])
        elif isinstance(data,list):
            for index in range(len(data)):
                data[index] = self.jsonify(data[index])
        try:
            data = json.loads(data)
        except:
            pass
        finally:
            return data

    def filter(self,data):
        if isinstance(data,list):
            for index in range(len(data)):
                self.filter(data[index])
        elif isinstance(data,dict):
            for key in data.keys():
                if data[key]=="Field NA" or data[key]=="Null":
                    del data[key]

class ImportExportView(BrowserView):
    """Import/Export page."""

    template = ViewPageTemplateFile('importexport.pt')

    # del EXCLUDED_ATTRIBUTES from data
    def exclude_attributes(self,data):
        if isinstance(data,dict):
            for key in data.keys():
                if key in EXCLUDED_ATTRIBUTES:
                    del data[key]
                    continue
                if isinstance(data[key],dict):
                    self.exclude_attributes(data[key])
                elif isinstance(data[key],list):
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
                path.append(urlparse(id_['@id']).path)

        # del EXCLUDED_ATTRIBUTES from data
        self.exclude_attributes(data)

        data['path'] = path_
        if data['@type']!="Plone Site":
            results = [data]
        for member in obj.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type!="Plone Site":
                results += self.serialize(member,path[0])
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
                ''' invokeFactory() is more generic, it can be used for any type of content, not just Dexterity content
                and it creates a new object at http://localhost:8080/self.context/new_id '''

                new_id = obj.invokeFactory(type_, new_id, title=title)
            except BadRequest as e:
                # self.request.response.setStatus(400)
                return 'DeserializationError {}'.format(str(e.message))
            except ValueError as e:
                # self.request.response.setStatus(400)
                return 'DeserializationError {}'.format(str(e.message))

        # restapi expects a string of JSON data
        data = json.dumps(data)
        # creating a spoof request with data embeded in BODY attribute, as expected by restapi
        request = UserDict.UserDict(BODY=data)
        # binding request to BrowserRequest
        zope.interface.directlyProvides(request, IBrowserRequest)

        # context must be the parent request object
        context = obj[new_id]

        deserializer = queryMultiAdapter((context, request), IDeserializeFromJson)
        try:
            deserializer()
            # self.request.response.setStatus(201)
            return "Success for {} \n".format(path)
        except DeserializationError as e:
            # self.request.response.setStatus(400)
            # pdb.set_trace()
            return "DeserializationError {0} {1} \n".format(str(e),path)
        except:
            # pdb.set_trace()
            return "DeserializationError {0} {1} \n".format(str('e'),path)

    def export(self):

        # create zip in memory
        self.zip = InMemoryZip()

        # defines Pipeline
        self.conversion = Pipeline()

        if self.request.method == 'POST':

            # get home_path of Plone sites
            url = self.request.URL
            id_ = urlparse(url).path.split('/')[1]
            home_path = '/' + id_

            # pdb.set_trace()
            # results is a list of dicts
            results = self.serialize(self.context, home_path)

            self.conversion.convertjson(self,results)

            self.request.RESPONSE.setHeader('content-type', 'application/zip')
            cd = 'attachment; filename=%s.zip' % (id_)
            self.request.RESPONSE.setHeader('Content-Disposition', cd)

            return self.zip.read()

        return

    def getparentcontext(self,data):
        path_ = data['path'].split('/')

        obj = self.context

        # traversing to the desired folder
        for index in range(2,len(path_)-1):
            obj = obj[path_[index]]

        return obj

    def imports(self):

        # create zip in memory
        self.zip = InMemoryZip()

        # defines Pipeline
        self.conversion = Pipeline()

        error_log = ''

        if self.request.method == 'POST':

            # TODO: implement mechanism for file upload
            zip_filename = '/home/shriyanshagro/Awesome_Stuff/Plone/zinstance/src/plone.importexport/src/plone/importexport/browser/Plone.zip'
            # json_data = self.readcsvasjson(csv_file)
            data = {"path": "/Plone/GSoC17", "description": "Just GSoC stuff", "@type":"Folder",'title':"GSoC17"
            # "id": "newfolder"
            }

            files = self.zip.getfiles(zip_filename)

            if not files:
                raise BadRequest('Please provide a good file')

            # get name of csv file
            for key in files.keys():
                if fnmatch.fnmatch(key,'*/*'):
                    pass
                elif fnmatch.fnmatch(key,'*.csv'):
                    csv_file = key

            # convert csv to json
            data = self.conversion.converttojson(files[csv_file])

            # filter out undefined keys
            self.conversion.filter(data)

            for index in range(len(data)):
                obj_data = data[index]

                if not obj_data['path']:
                    raise BadRequest("Property 'path' is required")


                # FIXME: solution for more than one image/file in an object
                if 'image' in obj_data.keys():
                    # pdb.set_trace()
                    if obj_data['image']['download'] in files.keys():
                        try:
                            content = files[obj_data['image']['download']].read()
                            obj_data['image']['data'] = content.encode("base64")
                            obj_data['image']['encoding'] = "base64"
                        except:
                            error_log += 'Error in fetching/encoding blob from zip {}'.format(obj_data['path'])

                if 'file' in obj_data.keys():
                    # pdb.set_trace()
                    if obj_data['file']['download'] in files.keys():
                        try:
                            content = files[obj_data['file']['download']].read()
                            obj_data['file']['data'] = content.encode("base64")
                            obj_data['file']['encoding'] = "base64"
                        except:
                            error_log += 'Error in fetching/encoding blob from zip {}'.format(obj_data['path'])


                # return parent of context
                parent_context = self.getparentcontext(obj_data)

                # all import error will be logged back
                error_log += self.deserialize(parent_context,obj_data)

        self.request.RESPONSE.setHeader(
            'content-type', 'application/text; charset=utf-8')
        return error_log

    def __call__(self):
        return self.template()
