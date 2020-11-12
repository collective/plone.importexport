====================
plone.importexport
====================

.. image:: https://travis-ci.org/collective/plone.importexport.svg?branch=master
    :target: https://travis-ci.org/collective/plone.importexport

Introduction
--------

This addon provides an end user way to provide reports or export CSVs on some or all of the content in your site. You have control 
over what content and what parts of that content is exported. If you want you can include file or html content in your export as a zip file.

In addition this plugin provides a way to take a CSV file and/or a zip of files and use this to update, create or sychronise content in your site.
Multiple methods of matching existing content and controlling the import are possible.

It will not allow users without permission to access more information that they can normally access or update information they can't update. A post import
report allows for understanding any permissions or validation errors during import.

Possible use cases include
- externally source data to be kept in sync with custom content types
- converting content from an existing site
- bulk updates of metadata of existing content by non technical users
- archiving a site or exporting the site in a format useful to some other CMS
- being able to generate reports on site content regardless of how its indexed.

Import/Export will work for any custom or builtin dexterity content type. It uses plone.restapi internally to ensure compatible import/export and mashalling.
Non-standard CSV data is handled by embedding json inside the CSV so export/export is losseless. In later releases there will be better handling of large imports and exports to reduce memory consumption and support for a long running process.

Installation
-------- 

- git clone https://github.com/collective/plone.importexport.git
- cd plone.importexport
- virtualenv .
- source bin/activate
- pip install -r requirements.txt

Build against the target version file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For example to build for Plone 5.1

- ./bin/buildout -c version_plone51.cfg
- ./bin/instance fg

USAGE
-------- 

The screen is accessible from Home_folder > Contents Tab > Action Menu.
This addon would be only be accessible to people who have designated permission to manipulate Plone site data.

UI
-------- 

Import/Export is currently an Actions menu item which applies to the current folder. In later releases this will be replace by a global control panel
with uses the query widget to specify content to export and what to match on content updates as well as where to place any new content on import.

The screen would propose two tabs: Basic and Advanced.

The **Basic tab** would allow to export all the folder and tree contents (and the result is immediately downloaded), or to import contents by uploading files (about the data format see below).

The **Advanced tab** would allow to do the same but also to choose:
- to include (or not) certain fields like-
   - dates
   - description
   - rights
   - workflow state
   - the fields to export/import, (based on schemas of locally addable types)
- to choose the data format (Only csv or only files or both?)(Export)
- action to take if content already exists (ignore, update, rename) (import)
- dry run mode (import)

After an import a downloadable report file will be provided of how many objects created, updated, ignored and error occured during the process.

Data format of Export
--------

The default data format for export would be a .zip containing: 

- a single CSV file with all the metadata. When fields aren't text, numbers or dates, quoted json will be used.
e.g.
```
path, title, description, authors_json, ...
"/folder1/page1", "A page", "blah, blah", "['shriyanshagro','franco']",..
```
- a set of separated files containing the actual inner contents: attached files + rich text (as HTML files), folders are represented as folders.

- a log file reporting error(if occured any) during the export of any field/object 

Note: we propose to use CSV as a default format because standard users are more likely to open/edit/manipulate CSV files rather than JSON.

Data format for Import
--------

User can upload multiple files at a time, which primarily allow them to update mutiple BLOB files in a single import.
Note: Multiple file upload doesn't mean Multiple Folder uploads

Min requirement:
   - A csv file containing metadata
   - Mandatory fields in csv are - {'@type', 'path', 'id', 'UID'} #TODO: There should be no min. Any field can be used to match and update. path is all thats needed for creation.

This import module creates a tree like directory structure of uploaded files, folder and zip.
Eg. if a file image.jpg is to be imported in News folder. Then it should be uploaded inside a news folder

The required csv file should be at root of tree. # TODO: CSV should be able to be uploaded without a zip.

If a zip file is uploaded(alone/along with other files), it will be unzipped by the addon and zip content will be added to the tree structure. After unzipping the zip:
   - accepted path structure for csv = anyname.csv
   - unaccepted path structure for csv= BLABLA/anyname.csv
        
Risks
--------

This addon has a few open issues, which are closely related to import functionality. So at current status a full import would not be possible and errors will be logged in an import-log file.

Test
--------

This addon has significant test coverage of module.
To perform tests, run this command:
   - `./bin/test -s plone.importexport -t test_importexport`
