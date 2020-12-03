# -*- coding: UTF-8 -*-
import csv
import cStringIO
import fnmatch
import json
import logging
import operator
import os
import zipfile
import StringIO

from bs4 import BeautifulSoup
from plone import api
from plone.uuid.interfaces import IUUID

from plone.importexport.exceptions import ImportExportError
from plone.importexport.interfaces import IImportExportSettings

log = logging.getLogger()


def remove_from_list(ls, val):
    if val in ls:
        ls.remove(val)


def get_metadata_pKeys():
    """ Get metadata fields that are allowed to be used as the primary key.
    """
    
    catalog = api.portal.get_tool('portal_catalog')
    default_ = set(catalog.indexes())
    exclude_metafields = set([
        'total_comments', 'effectiveRange', 'object_provides', 'commentators',
        'Type', 'cmf_uid', 'is_folderish', 'sync_uid', 'getId', 'meta_type',
        'is_default_page', 'Date', 'review_state', 'portal_type', 'expires',
        'allowedRolesAndUsers', 'getObjPositionInParent', 'in_reply_to',
        'effective', 'created', 'Creator', 'modified', 'sortable_title',
        'getRawRelatedItems', 'Subject', 'start', 'end', 'SearchableText',
        'path'
    ])
    return ['path'] + list(default_ - exclude_metafields)


class InMemoryZip(object):

    def __init__(self):

        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()

    def append(self, filename_in_zip, file_contents):
        """Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip."""
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(
            self.in_memory_zip,
            'a',
            zipfile.ZIP_DEFLATED,
            False,
        )

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0

    def read(self):
        """Returns a string with the contents of the in-memory zip."""
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def getfiles(self, zip_file):
        # TODO validate zip_file,files,csv_file and raise if not good file
        # TODO also for csv check MUST_INCLUDED_ATTRIBUTES
        if not zip_file:
            raise ImportExportError('No file Provided')
        data = {}
        """ The problem in the standard zipfile module is that when passed
        a file object (not a filename), it uses that same passed-in file
        object for every call to the open method. This means that tell and
        seek are getting called on the same file and so trying to open multiple
        files within the zip file is causing the file position to be shared and
        so multiple open calls result in them stepping all over each other. In
        contrast, when passed a filename, open opens a new file object.
        error: *** BadZipfile: Bad CRC-32 for file 'Plone.csv'
        There I realized if I do a seek(0) on the file object before
        initializing the ZipFile, the error goes away. Don't see why, as I did
        nothing before on the file object :/ """
        zip_file.seek(0)
        zfile = zipfile.ZipFile(zip_file, 'r')
        for name in zfile.namelist():
            """ .open() returns a file-like object while .read() return a string
            like object and csv.DictWriter needs a file like object """
            # FIXME .open() should work.
            # May be after retriving data from /tmp in the server may solve
            # this HACK
            data[name] = cStringIO.StringIO()
            data[name].write(zfile.read(name))
            data[name].seek(0)
        return data


class Pipeline(object):

    def getcsvheaders(self, data=None):
        """Return unique keys drom list."""
        header = {}
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
        return result

    def convertjson(self, obj, data_list, csv_headers):
        """Convert json list to into zip of csv and BLOB."""
        csv_output = cStringIO.StringIO()

        id_ = obj.context.absolute_url_path()[1:]

        # check type of export requested
        if obj.request.get('exportFormat', None):
            exportType = obj.request.get('exportFormat', None)
        else:
            exportType = 'combined'

        try:
            """The optional restval parameter specifies the value to be written
            if the dictionary is missing a key in fieldnames. If the
            dictionary passed to the writerow() method contains a key not
            found in fieldnames, the optional extrasaction parameter indicates
            what action to take. If it is set to 'raise' a ValueError is
            raised. If it is set to 'ignore', extra values in the dictionary
            are ignored."""
            writer = csv.DictWriter(
                csv_output,
                fieldnames=csv_headers,
                restval='Field NA',
                extrasaction='ignore',
                dialect='excel',
            )
            writer.writeheader()

            for data in data_list:
                for key in data.keys():
                    if not data[key]:
                        data[key] = 'Null'
                        continue

                    if exportType == 'files' or exportType == 'combined':
                        data[key] = self.getblob(obj, data[key], data['path'])

                        # converting list and dict to quoted json
                        data[key] = json.dumps(data[key])
                writer.writerow(data)
        except IOError as e:
                log.error('I/O error(%s): %s', e.errno, e.strerror)
        else:
            if exportType == 'csv' or exportType == 'combined':
                obj.zip.append(id_ + '.csv', csv_output.getvalue())

        csv_output.close()
        return

    def getblob(self, obj, data, path_):
        # store blob content and replace url with path
        if (isinstance(data, dict) and data.get('download', None)):
            file_path = path_
            relative_filepath = os.path.join(
                *file_path.split(os.sep)[1:])

            try:
                # REVIEW does separator for content-type here
                # also depends on os.sep?
                if data['content-type'].split('/')[0] == 'image':
                    file_data = obj.context.restrictedTraverse(
                        str(relative_filepath) + os.sep + 'image').data
                else:
                    file_data = obj.context.restrictedTraverse(
                        str(relative_filepath) + os.sep + 'file').data
            except Exception as e:
                log.error('Blob data fetching error')
                log.error(e.message)
            else:
                filename = data['filename']
                data['download'] = os.path.join(
                    file_path, filename)
                obj.zip.append(data['download'],
                               file_data)

        # '''store html files and replace key[data] with
        #     key[download], value= path in zip'''
        elif (isinstance(data, dict) and data.get('data', None)):
            file_path = path_

            try:
                # REVIEW does separator for content-type
                # here also depends on os.sep?
                if data['content-type'].split('/')[1] == 'html':
                    file_data = data['data'].encode(data['encoding'])
                    del data['data']
            except Exception as e:
                log.error('html data fetching error')
                log.error(e.message)
            else:
                filename = file_path.split(os.sep)[-1] + '.html'
                data['download'] = os.path.join(file_path, filename)
                obj.zip.append(data['download'], file_data)

        return data

    def converttojson(self, data=None, header=None):
        if not data:
            raise ImportExportError('Provide data to jsonify')
        # A major BUG here
        # The fieldnames parameter is a sequence whose
        # elements are associated with the fields of the input data in order
        reader = csv.DictReader(data, fieldnames=None)
        data = []
        for row in reader:
            for key in row.keys():
                if not key:
                    del row[key]
            data.append(row)
        # jsonify quoted json values
        data = self.jsonify(data)

        # filter keys which are not in header, feature of advance_import
        if header:
            for index in range(len(data)):
                for k in data[index].keys():
                    if k not in header:
                        del data[index][k]

        self.filter_keys(data)
        return data

    def jsonify(self, data):
        """Jsonfy quoted json values."""
        if isinstance(data, dict):
            for key in data.keys():
                data[key] = self.jsonify(data[key])
        elif isinstance(data, list):
            for index in range(len(data)):
                data[index] = self.jsonify(data[index])
        try:
            data = json.loads(data)
        # TODO raise the error into log_file
        except Exception:
            pass
        finally:
            return data

    def filter_keys(self, data=None, excluded=None):
        if isinstance(data, list):
            for index in range(len(data)):
                self.filter_keys(data[index], excluded)
        elif isinstance(data, dict):
            for key in data.keys():
                if data[key] == 'Field NA' \
                        or data[key] == 'Null' \
                        or (excluded and key in excluded):
                    del data[key]

        return True

    def fillblobintojson(self, obj_data, files, UIDmapping):  # NOQA: C901

        self.mapping = UIDmapping
        error_log = ''

        # FIXME: solution for more than one image/file in an object

        if obj_data.get('image', None):
            value = obj_data['image'].get('download', None)
            if value and files.get(value, None):
                try:
                    content = files[value].read()
                    obj_data['image']['data'] = content.encode('base64')
                    obj_data['image']['encoding'] = 'base64'
                except Exception:
                    error_log += ("""Error in fetching/encoding blob
                    from zip {arg}""".format(arg=obj_data['path']))

        if obj_data.get('file', None):
            value = obj_data['file'].get('download', None)
            if value and files.get(value, None):
                try:
                    content = files[value].read()
                    obj_data['file']['data'] = content.encode('base64')
                    obj_data['file']['encoding'] = 'base64'
                except Exception:
                    error_log += ("""Error in fetching/encoding blob
                    from zip {arg}""".format(arg=obj_data['path']))
        data_ = obj_data.get('text', None)
        if  data_ and data_.get('content-type', None):
            type_ = data_.get('content-type', None).split('/')[-1]
            value = data_.get('download', None)
            if type_ == 'html' and value and files.get(value, None):
                try:
                    # decoding
                    file_data = files[value].read().decode(
                        data_['encoding'])

                    # replacing old_UID with new_uid
                    file_data = self.mapping.internallink(file_data)

                    # encoding
                    file_data = file_data.decode(
                        data_['encoding'])

                    data_['data'] = file_data

                    del data_['download']
                except Exception:
                    error_log += ("""Error in fetching/encoding blob
                    from zip {arg}""".format(arg=obj_data['path']))

        return obj_data, error_log


class mapping(object):

    def __init__(self, obj):
        self.mapping = {}
        self.obj = obj
        self.available_pKeys = get_metadata_pKeys()

    def getValueFromMetafield(self, key, data):
        metafields = {
            'subject': 'subjects',
        }
        lw_key = key.lower()
        return data.get(
            metafields.get(lw_key, lw_key),
            data.get(key, None)
        )

    def mapNewUID(self, content):

        for data in content:

            UID = data.get('UID', None)
            path = data.get('path', None)

            if path and UID:
                self.mapping[UID] = self.getUID(path)

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

    # replacing old_UID with new_uid, this method is only called for html data
    def internallink(self, data):

        soup = BeautifulSoup(data, 'html.parser')

        for link in soup.find_all('a'):

            linktype = link.get('data-linktype')

            if linktype == 'internal':
                oldUid = link.get('data-val')
                if self.mapping.get(oldUid):
                        link['href'] = 'resolveuid/' + str(
                            self.mapping[oldUid])
                        link['data-val'] = self.mapping[oldUid]
        return str(soup)


class fileAnalyse(object):

    def __init__(self, files):

        self.files = files
        self.csv_file = None
        # unzip the zip and restructure the dict
        self.reStructure()
        # TODO if no csv_file then make one dynamically to
        # support uploaded BLOB
        self.csv_file = self.findcsv()

    def getFiletype(self, filename=None):

        # HACK
        type_ = filename.split('.')[-1]
        return type_

    # return csv from uploaded files
    """
    After unzipping the zip
    accepted type = BLABLABBLA/name.csv
    unaccepted type = BLABLABBLA/name.csv/something
    """
    def findcsv(self):
        # the zip may also have csv content of site
        ignore = str('*' + os.sep + '*')
        for key in self.files.keys():
            if fnmatch.fnmatch(key, ignore):
                continue
            if fnmatch.fnmatch(key, "__MACOSX/*"):
                continue
            if fnmatch.fnmatch(key, '*.csv'):
                    if not self.csv_file:
                        self.csv_file = self.files[key]
                    else:
                        raise ImportExportError(
                            'More than 1 csv file provided, require only 1')

        return self.csv_file

    def getCsv(self):
        self.csv_file.seek(0)
        return self.csv_file

    # unzip the zip and restructure the dict
    def reStructure(self):
        tempFiles = {}
        for k in self.files.keys():
            type_ = self.getFiletype(k)
            if type_ == 'zip':
                zip_file = self.files[k]
                tempzip = InMemoryZip()
                zip_file = tempzip.getfiles(zip_file)
                for filename in zip_file.keys():
                    tempFiles[filename] = zip_file[filename]
                del self.files[k]
        self.files.update(tempFiles)

    def getFiles(self):
        return self.files
