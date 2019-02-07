# -*- coding: utf-8 -*-

from DateTime import DateTime
from plone import api
from plone.importexport import utils
from plone.importexport.exceptions import ImportExportError
from plone.restapi.interfaces import IDeserializeFromJson
from plone.restapi.interfaces import ISerializeToJson
from Products.Five import BrowserView
from random import randint
from zExceptions import BadRequest
from zope.component import queryMultiAdapter
from zope.publisher.interfaces.browser import IBrowserRequest

import json
import os
import UserDict
import zope


global MUST_EXCLUDED_ATTRIBUTES
global MUST_INCLUDED_ATTRIBUTES
# global files

# files = {}
# global uploadedfile
#
# uploadedfile = 'test'

# these attributes must be excluded while exporting
# BUG: plone.restapi doesn't support desearlization of layouts, thus
#     excluding it from the exported data
MUST_EXCLUDED_ATTRIBUTES = [
    'member',
    'parent',
    'items',
    'changeNote',
    '@id',
    'scales',
    'items_total',
    'table_of_contents',
    'layout',
]

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

    # this will del MUST_EXCLUDED_ATTRIBUTES from data till leaves of the tree
    def exclude_attributes(self, data):

        if isinstance(data, dict):
            for key in data.keys():

                if key in self.getExcludedAttributes():
                    del data[key]
                    continue

                if isinstance(data[key], dict):
                    self.exclude_attributes(data[key])
                elif isinstance(data[key], list):
                    for index in range(len(data[key])):
                        self.exclude_attributes(data[key][index])

    # Caution: last element of returned list is always a string of errors
    # This funciton serialize obj
    def serialize(self, obj):

        results = []
        errorLog = ''

        serializer = queryMultiAdapter((obj, self.request), ISerializeToJson)

        data = serializer()

        # del MUST_EXCLUDED_ATTRIBUTES from data
        self.exclude_attributes(data)

        data['path'] = str(obj.absolute_url_path()[1:])

        # record required data
        if data.get('@type', None) != 'Plone Site':
            results = [data]

        for member in obj.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type != 'Plone Site':
                try:
                    objData = self.serialize(member)
                    results += objData[:-1]
                    if objData[-1] != '':
                        errorLog += objData[-1]
                except Exception as e:
                    errorLog += str('Error: ' + repr(e) + ' for ' + str(
                        member.absolute_url_path()[1:]) + '\n')
        results.append(errorLog)
        return results

    # context == requested object, data=metadata for object in json string
    # existing content are identified by path and ignored if requested
    def deserialize(self, context, data):

        path = str(context.absolute_url_path()[1:])

        if self.request.get('actionExist', None) == 'ignore' and (path in self.existingPath):  # NOQA: E501
            return 'Ignoring existing content at {arg} \n'.format(arg=path)

        # deserializing review_state
        new_state = None
        if data.get('review_state', None):
            new_state = str(data['review_state'])

        # restapi expects a string of JSON data
        data = json.dumps(data)

        # creating a spoof request with data embeded in BODY attribute,
        #     as expected by restapi
        request = UserDict.UserDict(BODY=data)

        # binding request to BrowserRequest
        zope.interface.directlyProvides(request, IBrowserRequest)

        # using plone.restapi to deserialize
        deserializer = queryMultiAdapter((context, request),
                                         IDeserializeFromJson)

        try:
            deserializer()
            if new_state:
                state = str(api.content.get_state(obj=context, default=None))
                if new_state != state:
                    api.content.transition(obj=context, to_state=new_state)

            return 'Success for {arg} \n'.format(arg=path)

        except Exception as e:
            error = str('Error: ' + repr(e) + ' for ' + path + '\n')

        return error

    def export(self):

        global MUST_INCLUDED_ATTRIBUTES
        errors = []

        # create zip in memory
        self.zip = utils.InMemoryZip()

        # defines Pipeline
        self.conversion = utils.Pipeline()

        if self.request and self.request.method == 'POST':

            id_ = self.context.absolute_url_path()[1:]

            exportType = self.request.get('exportFormat', None)

            if self.request.get('exportFields', None) and (exportType == 'csv' or exportType == 'combined'):  # NOQA: E501

                # fields/keys to include
                headers = self.request.get('exportFields', None)
                # BUG in html checkbox input, which
                # send value as a string if only one value have been checked
                if isinstance(headers, str):
                    headers = [headers]
                headers = list(set(MUST_INCLUDED_ATTRIBUTES +
                                   headers))

            else:
                # 'No check provided. Thus exporting whole content'
                headers = self.getheaders()

            # MUST_INCLUDED_ATTRIBUTES must present in headers and that too
            # at first position of list
            for element in reversed(MUST_INCLUDED_ATTRIBUTES):
                headers.insert(0, element)

            # results is a list of dicts
            objData = self.serialize(self.context)
            results = objData[:-1]
            if objData[-1] != '':
                errorLog = objData[-1]
                self.zip.append('errorLog.txt', errorLog)

            self.conversion.convertjson(self, results, headers)
            self.request.RESPONSE.setHeader('content-type', 'application/zip')
            cd = 'attachment; filename={arg}.zip'.format(arg=str(id_))
            self.request.RESPONSE.setHeader('Content-Disposition', cd)

            return self.zip.read()

        else:
            raise ImportExportError('Invalid Request')

    # invoke non-existent content,  if any
    def createcontent(self, data):

        log = ''
        for index in range(len(data)):

            obj_data = data[index]

            if not obj_data.get('path', None):
                log += 'pathError in {arg}\n'.format(arg=obj_data['path'])
                continue

            if not obj_data.get('@type', None):
                log += '@typeError in {arg}\n'.format(arg=obj_data['path'])
                continue

            #  os.sep is preferrable to support multiple filesystem
            #  return parent of context
            obj = self.getobjcontext(
                obj_data['path'].split(os.sep)[:-1])

            if not obj:
                log += 'pathError, Parent object not found for {arg}\n'.format(
                    arg=obj_data['path'])
                continue

            id_ = obj_data.get('id', None)
            title = obj_data.get('title', None)
            type_ = obj_data.get('@type', None)

            # creating  random id
            if not id_:
                now = DateTime()
                new_id = '{arg1}.{arg2}.{arg3}{arg4:04d}'.format(
                    arg1=type_.lower().replace(' ', '_'),
                    arg2=now.strftime('%Y-%m-%d'),
                    arg3=str(now.millis())[7:],
                    arg4=randint(0, 9999))
                if not title:
                    title = new_id
            else:
                new_id = id_

            # check if context exist
            if not obj.get(new_id, None):

                    log += 'creating new object {arg}\n'.format(
                        arg=obj_data['path'].split(os.sep)[-1])

                    if not obj_data.get('@type', None):
                        log += 'typeError in {arg}\n'.format(
                            arg=obj_data['path'])
                        continue

                    # Create object
                    try:
                        # invokeFactory() is more generic, it can be used for
                        # any type of content, not just Dexterity content
                        # and it creates a new object at
                        # http://localhost:8080/self.context/new_id

                        new_id = obj.invokeFactory(type_, new_id, title=title)
                    except BadRequest as e:
                        # self.request.response.setStatus(400)
                        log += 'Error, BadRequest {arg}\n'.format(
                            arg=str(e.message))
                    except ValueError as e:
                        # self.request.response.setStatus(400)
                        log += 'ValueError {arg}\n'.format(arg=str(e.message))

        return log

    # get list of existingPath under given context
    def getExistingpath(self, context=None):

        if not context:
            context = self.context
            self.existingPath = []

        if context.portal_type != 'Plone Site':
            self.existingPath.append(str(context.absolute_url_path()[1:]))
            # self.existingPath.append(str(context))

        for member in context.objectValues():
            # FIXME: defualt plone config @portal_type?
            if member.portal_type != 'Plone Site':
                    self.getExistingpath(member)

        return self.existingPath

    #  provide list of path that occured in Plone server and dataPath
    def getCommonpath(self, dataPath):

        common = []
        tempPath = []
        # get list of existingPath
        self.getExistingpath()

        for path in dataPath:
            path = path.split(os.sep)[1:]
            path = os.sep.join(path)
            tempPath.append(path)

        for path in self.existingPath:
            path = path.split(os.sep)[1:]
            path = os.sep.join(path)

            if path in tempPath:
                common.append(path)

        return common

    # if creating new content against existing content
    #  provide list of path that occured in Plone server and uploaded csv
    def getCommancontent(self):

        # request files
        file_ = self.request.get('file')

        # files are at self.files
        self.files = {}
        self.requestFile(file_)

        # file structure and analyser
        self.files = utils.fileAnalyse(self.files)

        if not self.files.getCsv():
            matrix = {'Error': 'No csv Provided'}

            # JS requires json dump
            matrix = json.dumps(matrix)

            return matrix

        # get path form csv_file
        conversion = utils.Pipeline()
        jsonList = conversion.converttojson(
            data=self.files.getCsv(), header=['path'])

        path_ = []
        for element in jsonList:
            path_.append(element.get('path', None))

        common_path = self.getCommonpath(path_)

        return common_path

    # requires path list from root
    def getobjcontext(self, path):

        obj = self.context

        # traversing to the desired folder
        for element in path[1:]:
            try:
                obj = obj[element]
            except Exception:
                return None

        return obj

    def requestFile(self, file_):

        if isinstance(file_, list):
            for element in file_:
                    self.requestFile(element)

        else:
            file_.seek(0)
            if not file_.read():
                raise ImportExportError('Provide Good File')
            file_.seek(0)
            try:
                filename = file_.filename
            except Exception:
                filename = file_.name

            self.files[filename] = file_
            return True

    def imports(self):

        global MUST_EXCLUDED_ATTRIBUTES
        global MUST_INCLUDED_ATTRIBUTES
        # global files

        # try:
        if self.request.method == 'POST':

            # request files
            file_ = self.request.get('file')

            # files are at self.files
            self.files = {}
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
            data = self.conversion.converttojson(
                data=self.files.getCsv(), header=include)
            # invoke non-existent content,  if any
            error_log += self.createcontent(data)

            # map old and new UID in memory
            self.mapping.mapNewUID(data)

            # deserialize
            for index in range(len(data)):

                obj_data = data[index]

                if not obj_data.get('path', None):
                    error_log += 'pathError in {arg} \n'.format(
                        arg=obj_data['path'])
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
                    error_log += 'pathError for {arg}\n'.format(
                        arg=obj_data['path'])

            self.request.RESPONSE.setHeader(
                'content-type', 'application/text; charset=utf-8')
            return error_log

        else:
            raise ImportExportError('Invalid Request Method')

    # return headers of serialized self.context
    def getheaders(self):

        if self.exportHeaders:
            return self.exportHeaders

        objData = self.serialize(self.context)
        data = objData[:-1]
        if objData[-1] != '':
            errorLog = objData[-1]

        conversion = utils.Pipeline()
        head = conversion.getcsvheaders(data)

        self.exportHeaders = filter(
            lambda head: head not in MUST_INCLUDED_ATTRIBUTES, head)

        return self.exportHeaders

    # Below are the Helper functions to generate views

    # return matrix of headers
    def getmatrix(self, headers=None, columns=4):

        matrix = {}
        count = len(headers)
        rows = float(count / columns)

        if isinstance(rows, float):
            rows = int(rows) + 1

        for index in range(rows):
            matrix[index] = []
            for i in range(columns):
                if count < 1:
                    continue
                count -= 1
                matrix[index].append(headers[count])

        return matrix

    # returns matrix of headers for self.context
    def getExportfields(self):

        # get headers of self.context
        headers = self.getheaders()
        # in matrix form
        matrix = self.getmatrix(headers=headers, columns=4)

        return matrix

    # returns headers of imported csv file
    def getImportfields(self):

        global MUST_INCLUDED_ATTRIBUTES

        try:
            self.files = {}
            # request files
            file_ = self.request.get('file')
            # files are at self.files
            self.requestFile(file_)

            # file structure and analyser
            self.files = utils.fileAnalyse(self.files)

            if not self.files.getCsv():
                raise ImportExportError('Provide a good csv file')

            csvData = self.files.getCsv()
            # convert csv to json
            conversion = utils.Pipeline()
            jsonData = conversion.converttojson(data=csvData)
            # get headers from jsonData
            headers = conversion.getcsvheaders(jsonData)

            headers = filter(
                lambda headers: headers not in MUST_INCLUDED_ATTRIBUTES,
                headers)

            # get matrix of headers
            matrix = self.getmatrix(headers=headers, columns=4)

        except Exception as e:
            matrix = {'Error': e.message}

        # JS requires json dump
        matrix = json.dumps(matrix)
        return matrix

    def getExcludedAttributes(self):
        global MUST_EXCLUDED_ATTRIBUTES
        return MUST_EXCLUDED_ATTRIBUTES

    def getIncludedAttributes(self):
        global MUST_INCLUDED_ATTRIBUTES
        return MUST_INCLUDED_ATTRIBUTES
