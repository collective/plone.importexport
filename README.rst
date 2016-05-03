====================
plone.importexport
====================

Abstract
--------

Provide a method to allow an editor to import content, export content or move content securely between sites.

Motivation
----------

Exporting and importing content from a Plone site should be easy.
Tools like `transmogrifier` and `collective.jsonify` require a lot of programming skills.
This feature must be exposed through a simple UI.

There are a number scenarios where import/export of content is useful.

- User has created a site locally and now wants to put it into production
- User has staging server where they want to make wide ranging changes which get moved into production in a single transaction
  - also moving production content back into staging. ie resynching.
- When upgrades are too hard you might want to start afresh and move just the content over
- Cherry pick parts of the site to export
- Export selected metadata for auditing purposes
- Export of content into an external system
- Export of content or metadata to be filtered or modified before reimporting for a bulk update.
- Exporting from another source and importing content into plone.
- Allowing editors to import content where they have permission to add content.

The motivation is try and cover all of this with a single UI but if not the primary usecase is moving content between sites.


Assumptions
-----------

It might be relevant to re-use here the `plone.restapi` serialization.


Proposal & Implementation
-------------------------

See https://github.com/plone/Products.CMFPlone/issues/1373 for links to previous discussions

Scope
+++++

The import/export feature will be applicable to all the Plone 5 default content-types and any regular Dexterity type.
Note: Processing other content types or Dexterity types involving custom fields can be done by registering custom adapters.

UI
++

The screen is accessible from the Actions menu on any folder.
The screen would propose two tabs: Basic and Advanced.

The **Basic tab** would allow to export all the folder and tree contents (and the result is immediately downloaded), or to import contents by uploading a file (about the data format see below).

The **Advanced tab** would allow to do the same but also to choose:
- the types to export/import, (or maybe query)
- to exclude (or not) 
   - comments,
   - assigned portlets,
   - workflow state
   - sharing
   - content rule assignments
   - display view assignments
   - the fields to export/import, (based on schemas of locally addable types)
- to choose the exportation mode (browser upload/download or read/write in server ./var folder),
- to choose the data format.
- action to take if content already exists (stop, ignore, update, overwrite, rename) (import)
- dry run mode (import)

After import a report is given of how many objects created, updated etc.

Data format
+++++++++++

The default data format would be a .zip containing:
- a single CSV file with all the metadata. When fields aren't text, numbers or dates, json will be used.
e.g.
```
path, title, description, authors_json, ...
"/folder1/page1", "A page", "blah, blah", "['djay','hector']",..
```
- a set of separated files containing the actual inner contents: attached files + rich text (as HTML files), folders are represented as folders.

The Advanced tab will allow to choose a pure JSON format instead of the CSV format. It will be a .zip file containing:
- one file by object containing metadata + rich text fields,
- attached files as separated files.

If we choose to use the server ./var folder instead of upload/download, the files are not zipped.

Note: we propose to use CSV as a default format because standard users are more likely to open/edit/manipulate CSV files rather than JSON.

Security
++++++++

By default the corresponding permission will be assigned to Managers only.

As data can be exposed and manipulated in transit when uploading or downloading contents (see Risks), we just propose to add the following warning:
"If you choose to upload/download exported contents, be aware your data can be exposed and manipulated in transit. For a more secure procedure, prefer server local folder import/export mode."

Implementation details
++++++++++++++++++++++

Import / export processing must/should be done asynchroneously.

Data format
+++++++++++

1. Zip of json files, one per object
2. Single jsonlines file
3. Single json file (compatible with collective.jsonify)
4. Zip of files with primary field data (images, html etc) and metadata in single CSV file. Where fields aren't text, numbers or dates, json will be used.
5. Zip of files with primary field data (images, html etc) and metadata stored in a similarly named .json file
6. Zip of files with primary field data and metadata stored as RFC822 marshalling, compatible with current GS.


Deliverables
------------

- a new module named `plone.importexport` to implement the import and export core mechanism
- a new version of `Products.CMFPlone` providing the needed control panels
- documentation (note: the documentation will explain how to implement an import/export adapter in add-ons) 

Risks
-----

- To export all the data some internal data structures could be exposed and manipulated in transit.
  - could be mitigated by encrypting the data with a key from the target site before export.
  - could allow only managers to do full import, and lower users to only import fields they can normally edit.
- It might be possible for the data to be in an inconsistent state if manipulated. Validations can rely certain add forms and order or input.
- The order of creating content can lead to unexpected results if validation involves relationships between objects.
- Very large exports or exports can be expensive and
  - Might need a way to restrict by user or size
  - Might need to support resumable uploads
- Ops might like to prevent data being dumped or accessed from the server.
- Not allowing uploading partial metadata for bulk updates means other plugins would be needed to handle this usecase which would also be labeled import/export.
- A data format like json makes is harder for non technical users from being able to run reports on content metadata, filter content before upload, change content before upload, take data out of other systems and import as content.
  - could use combination of csv and json (such as data format 4) to allow some metadata manipulated using a spreadsheet, while still supporting complex data structures.
