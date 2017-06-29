import os
from urlparse import urlparse
import csv
import StringIO
import cStringIO
import zipfile
import operator
import json
import pdb
from plone.uuid.interfaces import IUUID


class InMemoryZip(object):

    def __init__(self):

        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a",
                             zipfile.ZIP_DEFLATED, False)

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

    def getfiles(self, zip_file):
        data = {}
        '''The problem in the standard zipfile module is that when passed
        a file object (not a filename), it uses that same passed-in file
        object for every call to the open method. This means that tell and
        seek are getting called on the same file and so trying to open multiple
        files within the zip file is causing the file position to be shared and
        so multiple open calls result in them stepping all over each other. In
        contrast, when passed a filename, open opens a new file object.
        error: *** BadZipfile: Bad CRC-32 for file 'Plone.csv'
        There I realized if I do a seek(0) on the file object before
        initializing the ZipFile, the error goes away. Don't see why, as I did
        nothing before on the file object :/'''
        zip_file.seek(0)
        zfile = zipfile.ZipFile(zip_file, 'r')
        for name in zfile.namelist():
            '''.open() returns a file-like object while .read() return a string like object
            And csv.DictWriter needs a file like object'''
            # FIXME .open() should work.
            # May be after retriving data from /tmp in the server may solve
            # this HACK
            data[name] = cStringIO.StringIO()
            data[name].write(zfile.read(name))
            data[name].seek(0)
        return data


class Pipeline(object):

    # return unique keys from list
    def getcsvheaders(self, data):
        # HACK to keep these fields at first in csv
        header = {'@type': 3, 'path': 2, 'id': 1}
        for dict_ in data:
            for key in dict_.keys():
                if key not in header.keys():
                    header[key] = 1
                else:
                    header[key] += 1

        result = []
        header = sorted(header.items(), key=operator.itemgetter(1),
                        reverse=True)
        for key in header:
            result.append(key[0])
        # pdb.set_trace()
        return result

    def convertjson(self, obj, data_list):
        csv_output = cStringIO.StringIO()

        url = obj.request.URL
        id_ = urlparse(url).path.split('/')[1]

        csv_headers = self.getcsvheaders(data_list)

        if not csv_headers:
            raise BadRequest("check json data, no keys found")

        try:
            '''The optional restval parameter specifies the value to be written
            if the dictionary is missing a key in fieldnames. If the
            dictionary passed to the writerow() method contains a key not
            found in fieldnames, the optional extrasaction parameter indicates
            what action to take. If it is set to 'raise' a ValueError is
            raised. If it is set to 'ignore', extra values in the dictionary
            are ignored.'''
            writer = csv.DictWriter(csv_output, fieldnames=csv_headers,
                                    restval='Field NA', extrasaction='raise',
                                    dialect='excel')
            writer.writeheader()
            for data in data_list:
                for key in data.keys():
                    if not data[key]:
                        data[key] = "Null"
                    if isinstance(data[key], (dict, list)):

                        # store blob content and replace url with path
                        if (isinstance(data[key], dict) and
                                data[key].get('download', None)):
                            # pdb.set_trace()

                            file_path = data['path']
                            relative_filepath = os.path.join(
                                *file_path.split('/')[1:])

                            try:
                                if data[key]['content-type'].split(
                                            '/')[0] == 'image':
                                    file_data = obj.context.restrictedTraverse(
                                        str(relative_filepath)+'/image').data
                                else:
                                    file_data = obj.context.restrictedTraverse(
                                        str(relative_filepath)+'/file').data
                            except:
                                print 'Blob data fetching error'
                            else:
                                filename = data[key]['filename']
                                # pdb.set_trace()
                                data[key]['download'] = os.path.join(
                                    file_path, filename)
                                obj.zip.append(data[key]['download'],
                                               file_data)

                        # '''store html files and replace key[data] with
                        #     key[download], value= path in zip'''
                        elif (isinstance(data[key], dict) and
                                data[key].get('data', None)):
                            # pdb.set_trace()

                            file_path = data['path']

                            try:
                                # pdb.set_trace()
                                if data[key]['content-type'].split(
                                            '/')[1] == 'html':
                                    file_data = data[key]['data'].encode(
                                                    data[key]['encoding'])
                                    del data[key]['data']
                            except:
                                print 'html data fetching error'
                            else:
                                filename = file_path.split('/')[-1]+'.html'
                                data[key]['download'] = os.path.join(
                                                        file_path, filename)
                                obj.zip.append(data[key]['download'],
                                               file_data)

                    # converting list and dict to quoted json
                    data[key] = json.dumps(data[key])

                writer.writerow(data)
        except IOError as (errno, strerror):
                print("I/O error({0}): {1}".format(errno, strerror))
        else:
            obj.zip.append(id_+'.csv', csv_output.getvalue())
            csv_output.close()

        return

    def converttojson(self, data):
        reader = csv.DictReader(data)
        data = []
        for row in reader:
            data.append(row)
        # jsonify quoted json values
        data = self.jsonify(data)
        return data

    # jsonify quoted json values
    def jsonify(self, data):
        if isinstance(data, dict):
            for key in data.keys():
                data[key] = self.jsonify(data[key])
        elif isinstance(data, list):
            for index in range(len(data)):
                data[index] = self.jsonify(data[index])
        try:
            data = json.loads(data)
        # TODO raise the error into log_file
        except:
            pass
        finally:
            return data

    def filter(self, data):
        if isinstance(data, list):
            for index in range(len(data)):
                self.filter(data[index])
        elif isinstance(data, dict):
            for key in data.keys():
                if data[key] == "Field NA" or data[key] == "Null":
                    del data[key]

        return True

    def fillblobintojson(self, data, files, UIDmapping):

        # pdb.set_trace()
        self.mapping = UIDmapping
        error_log = ''
        for index in range(len(data)):

            obj_data = data[index]

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
                        content = files[value].read()
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
                        # decoding
                        file_data = files[value].read().decode(
                            obj_data['text']['encoding'])

                        # replacing old_UID with new_uid
                        file_data = self.mapping.internallink(file_data)

                        # encoding
                        file_data = file_data.encode(
                            obj_data['text']['encoding'])

                        obj_data['text']['data'] = file_data

                        del obj_data['text']['download']
                    except:
                        error_log += ('''Error in fetching/encoding blob
                        from zip {}'''.format(obj_data['path']))

            data[index] = obj_data

        return data, error_log


class mapping(object):

    def __init__(self, obj):
        self.mapping = {}
        self.obj = obj

    def mapNewUID(self, content):

        # pdb.set_trace()
        for data in content:

            UID = data.get('UID', None)
            path = data.get('path', None)

            if path and UID:
                self.mapping[UID] = self.getUID(path)

            else:
                # TODO raise error_log here
                continue

        return self.mapping

    def getUID(self, path):
        """ AT and Dexterity compatible way to extract UID from a
         content item """

        # Make sure you don't get UID from parent folder accidentally
        context = self.obj.getobjcontext(path.split(os.sep))

        # Returns UID of the context or None if not available
        # Note that UID is always available for all Dexterity 1.1+
        # content and this only can fail if the content is old not migrated
        uuid = IUUID(context, None)
        return uuid

    # replacing old_UID with new_uid
    def internallink(self, data):
        for uid in self.mapping.keys():
            data = data.replace(uid, self.mapping[uid])
        return data
