import os
import json
import sys
import transaction
import yaml
from base64 import b64decode
from DateTime import DateTime

from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.factory import addPloneSite
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.container.interfaces import INameChooser
from Acquisition import aq_inner
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from plone import api
from Testing.makerequest import makerequest
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.portlet.static import static
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.uuid.interfaces import ATTRIBUTE_NAME
from zope.component.hooks import setSite
from zExceptions import BadRequest
from DateTime.DateTime import DateTime
from zope.component._api import getUtility, getMultiAdapter, queryMultiAdapter
from plone.portlets.interfaces import ILocalPortletAssignmentManager, IPortletAssignmentSettings
from zope.container.interfaces import INameChooser
from Products.CMFPlone.utils import safe_unicode
import datetime

from zope import event
from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from types import ListType
from plone.portlets.constants import GROUP_CATEGORY, CONTENT_TYPE_CATEGORY, \
    CONTEXT_CATEGORY

site_id = sys.argv[3]
if site_id in app.objectIds():
    print "The {} Plone site was found".format(site_id)
else:
    print "No Plone site was found with id {}".format(site_id)
    sys.exit(1)


# Sets the current site as the active site
setSite(app[site_id])
portal = api.portal.get()

path_ = "content"

# Get JSON files.
json_files = ["{}/{}".format(path_,item) for item in os.listdir(path_) if item.endswith(".json")]
portlet_files = ["{}/{}".format(path_,item) for item in os.listdir(path_) if item.endswith(".portlet.yaml")]


custom_layouts_by_id = {
    "337cf624310f4f58b426375f0ddf6472": "collection_gallery_view"
}

def addPortlet(context, columnName='plone.leftcolumn', portlet=None):
    """ code borrowed from
        https://github.com/collective/wm.sampledata/blob/3146f22bf82f60924766997b5106cf03b8cd27c8/wm/sampledata/utils.py
    """
    if not portlet:
        return

    column = getUtility(IPortletManager, columnName)
    manager = getMultiAdapter((context, column),IPortletAssignmentMapping)
    chooser = INameChooser(manager)
    manager[chooser.chooseName(None, portlet)] = portlet

def importZEXP(context,name,path="content"):
    """ this importer by default imports scripts from a
        folder named 'content' """
    zexp = context._p_jar.importFile('{}/{}.zexp'.format(path,name))
    context._setObject(name,zexp)
    transaction.commit()

def setCustomLayout(obj, id, default=None):
    layout = custom_layouts_by_id.get(id, None)
    if layout:
        obj.setLayout(layout)
        obj.layout = layout
        obj.reindexObject(idxs=['layout'])
    elif default:
        if "collective.listingviews" in default:
            default = "listing_view"
        obj.setLayout(default)

def setImageData(obj, data):
    if "image" in data:
        obj.image = data["image"]
    if "imageCaption" in data:
        obj.imageCaption = data["imageCaption"]
    if '_datafield_image' in data:
        image_data = data['_datafield_image']
        obj.image = prep_image(
             imagename=image_data['filename'],
             data=image_data['data'],
             content_type=image_data['content_type'],
            )

def setTransition(obj, data):
    # grab the most recent workflow and transition action
    wf = data['_workflow_history'].items()[0][1]
    transition = wf[-1]['action']
    if transition in ["reject","retract"]:
        # it is already private by default
        pass
    elif transition:
        print "==== transition {}".format(transition)
        api.content.transition(obj=obj,
                           transition=transition,
                           comment='Transition, initiated by import script'
                           )


def get_level(files):
    data_levels = {}
    level = 1
    for json_file in json_files:
        if not json_file.endswith(".json"):
            print "skipped {}. It doesn't end with .json".format(json_file)
            continue
        print "loading {}".format(json_file)
        with open(json_file) as data_file:
            data = json.load(data_file)
            path_len = len(data['_path'].split('/'))
            level = path_len - 2
            if level not in data_levels:
                data_levels[level] = [[json_file, data]]
            else:
                data_levels[level].append([json_file, data])
    return data_levels


def import_data_levels(data_levels):
    for level, data in data_levels.items():
        print "========================================="
        print "----------> Creating level %d objects" % (level)
        for datum in data:
            create_object(level, datum)
        transaction.commit()
        print "========================================="


def create_object(level, data):
    json_data = data[1]
    json_file = data[0]
    path_ = json_data['_path']
    type = json_data['_type']
    if 'title' in json_data:
        name = json_data['title']
    else:
        print "{} has no title".format(json_file)
        return
    id = json_data['_id']
    base_path = "".join(path_.split('/Plone')[1:])
    args = {
        "level": level,
        "id": id,
        "base_path": base_path,
        "name": name,
        "data": json_data,
        "path_": path_
    }
    if type == "Folder" and id != "carousel":
        print json_file,"*****"
        create_folder(**args)
    elif type == "Collection":
        create_collection(**args)
    elif type == "News Item":
        create_news_item(**args)
    elif type == "Document":
        create_document(**args)
    elif type == "destination":
        create_destination(**args)
    elif type == "Link":
        create_link(**args)
    elif type == "Image":
        create_image(**args)
    elif type == "File":
        create_file(**args)

def create_folder(level, id, base_path, path_, name, data):
    container = api.portal.get()
    if level > 1:
        parent = data['_path'].split('/')[-2]
        _path = "/".join(base_path.split('/')[:-1])
        container = api.content.get(path=_path)
    if not container:
        print "el container",container, "***"
        return
    if id not in container:
        otherdata =  {
            "exclude_from_nav": data.get("excludeFromNav", False),
            "description": data["description"],
            "defaultpage": data["_defaultpage"],
            "subject": data["subject"],
         }
        obj = api.content.create(
            type='Folder',
            title=name,
            id=id,
            safe_id=False,
            container=container,
            **otherdata)
        if data.get("_defaultpage", False):
            obj.setDefaultPage(data["_defaultpage"])
        setCustomLayout(obj=obj, id=id, default=data['_layout'])
        if "travel-info" not in data['_path']:
            print("... blocking left parent portlets on {}".format(
                                                                data['_path']))
            blockPortlets(obj, columnName='plone.leftcolumn', inherited=True)
        setTransition(obj, data)
        set_dates(obj,data)
        setuid(obj, data['_uid'])
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)


def create_collection(level, id, base_path, path_, name, data):
    container = api.portal.get()
    _path = base_path
    if level > 1:
        parent = data['_path'].split('/')[-2]
        _path = "/".join(base_path.split('/')[:-1])
        container = api.content.get(path=_path) or container
    if id in container:
        # get rid of it, since we want to create it
        old_obj = api.content.get(path=_path)
        api.content.delete(obj=old_obj, check_linkintegrity=False)
    if id not in container:

        collection_data =  {
            "exclude_from_nav":True,
            "contributors":data["contributors"],
            "text":RichTextValue(data["text"]),
            "allowDiscussion":data["allowDiscussion"],
            "query":data["query"],
            "sort_on":data["sort_on"],
            "description":data["description"],
            "customViewFields":data["customViewFields"],
            "sort_reversed":data["sort_reversed"],
            "tableContents":data["tableContents"],
            "limit":data["limit"],
            "presentation":data["presentation"],
            "defaultpage": data["_defaultpage"],
            "subject":data["subject"],
            "atrefs":data.get("_atrefs", {}),
         }

        obj = api.content.create(
            type="Collection",
            title=name,
            id=id,
            safe_id=False,
            container=container,
            **collection_data
        )
        set_dates(obj, data)
        setCustomLayout(obj, id=id, default=data['_layout'])
        setuid(obj, data['_uid'])
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)


def create_document(level, id, base_path, path_, name, data):
    container = api.portal.get()
    if level > 1:
        parent = data['_path'].split('/')[-2]
        _path = "/".join(base_path.split('/')[:-1])
        container = api.content.get(path=_path)
    if container and id not in container:
        otherdata =  {
            "exclude_from_nav":True,
            "contributors":data["contributors"],
            "text":RichTextValue(data["text"]),
            "allowDiscussion":data["allowDiscussion"],
            "description":data["description"],
            "atrefs":data.get("_atrefs", {}),
            "subject":data["subject"],

         }
        obj = api.content.create(
            type="Document",
            title=name,
            id=id,
            safe_id=False,
            container=container,
            **otherdata
        )
        set_dates(obj, data)
        setuid(obj, data['_uid'])
        transition = data['_workflow_history']['simple_publication_workflow'][-1]['action']
        if transition in ["reject","retract"]:
            # it is already private by default
            pass
        elif transition:
            print "==== transition {}".format(transition)
            api.content.transition(obj=obj,
                               transition=transition,
                               comment='Transition, initiated by import script'
                               )
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)


def create_destination(level, id, base_path, path_, name, data):
    container = api.portal.get()
    if level > 1:
        parent = data['_path'].split('/')[-2]
        _path = "/".join(base_path.split('/')[:-1])
        container = api.content.get(path=_path)
    if container and id not in container:
        otherdata =  {
            "exclude_from_nav":True,
            "contributors":data["contributors"],
            "description":data["description"],
            "location":data["location"],
            "image_side_text":data["image_side_text"],
            "blurb2":data["blurb2"],
            "blurb1":data["blurb1"],
            "fly_to_message":data["fly_to_message"],
            "atrefs":data.get("_atrefs", {}),

         }
        obj = api.content.create(
            type="destination",
            title=name,
            id=id,
            safe_id=False,
            container=container,
            **otherdata
        )
        setuid(obj, data['_uid'])
        setImageData(obj, data)
        setTransition(obj, data)
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)

def create_link(level, id, base_path, path_, name, data):
    container = api.portal.get()
    if level > 1:
        parent = data['_path'].split('/')[-2]
        _path = "/".join(base_path.split('/')[:-1])
        container = api.content.get(path=_path)
    try:
        if id not in container:
            otherdata =  {
                "exclude_from_nav":True,
                "contributors":data["contributors"],
                "allowDiscussion":data["allowDiscussion"],
                "description":data["description"],
                "remoteUrl":data["remoteUrl"],
             }
            obj = api.content.create(
                type="Link",
                title=name,
                id=id,
                safe_id=False,
                container=container,
                **otherdata
            )
            set_dates(obj, data)
            setuid(obj, data['_uid'])
    except TypeError as e:
        print "############### error #####################"
        print e
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)


def create_news_item(level, id, base_path, path_, name, data):
    otherdata = {
        "exclude_from_nav":True,
        "contributors":data["contributors"],
        "text":RichTextValue(data["text"]),
        "allowDiscussion":data["allowDiscussion"],
        "description":data["description"],
        "atrefs":data.get("_atrefs", {})
    }
    _path = "/".join(base_path.split('/')[:-1])
    if level > 1:
        container = api.content.get(path=_path)
    else:
        container = api.portal.get()
    if container and id not in container:
        obj = newsitem = api.content.create(
            type='News Item',
            title=name,
            id=id,
            safe_id=False,
            container=container,
            **otherdata)
        setCustomLayout(obj=obj, id=id, default=data['_layout'])
        set_dates(obj, data)
        obj.reindexObject()
        setuid(obj, data['_uid'])
        setImageData(obj, data)
        setTransition(obj, data)
    else:
        print "content already present for {}".format(base_path)
    print "type is :{}, path is:{},{}".format(data['_type'],
                         data['_path'], level + 2)


def create_file(level, id, base_path, path_, name, data):
    file_data = data['_datafield_file']
    if 'title' in data:
        if data['title'] != "":
            name = data['title']
        else:
            name = file_data['filename']
    otherdata = {
             "contributors":data["contributors"],
             "allowDiscussion":data["allowDiscussion"],
             "atrefs":data.get("_atrefs", {}),
             }
    _path = "/".join(base_path.split('/')[:-1])
    if level == 1:
        container = api.portal.get()
    else:
        container = api.content.get(path=_path)
    if container and id not in container:
        file_obj = api.content.create(
            type='File',  # set the content type
            container=container,
            title=name,
            id=id,
            **otherdata)

        name=file_data['filename']
        uid = data['_uid']
        setuid(file_obj, uid)
        set_dates(file_obj, data)
        file_obj.file = prep_file(
                                name=name,
                                data=file_data['data'],
                                content_type=file_data['content_type'],
                               )
        file_obj.reindexObject()
    else:
        print "image already present for {}".format(base_path)

def create_image(level, id, base_path, path_, name, data):
    if 'title' in data:
        name = data['title']
    else:
        print "{} has no title".format(json_file)
        return
    image_data = data['_datafield_image']
    otherdata = {
             "contributors":data["contributors"],
             "allowDiscussion":data["allowDiscussion"],
             "atrefs":data.get("_atrefs", {}),
             }
    _path = "/".join(base_path.split('/')[:-1])
    if level == 1:
        container = api.portal.get()
    else:
        container = api.content.get(path=_path)
    # delete the image if it exists
    if container and id in container:
        api.content.delete(obj=container[id], check_linkintegrity=False)
    if container and id not in container:
        image_obj = api.content.create(
            type='Image',  # set the content type
            container=container,
            title=name,
            id=id,
            **otherdata)

        imagename=image_data['filename']
        uid = data['_uid']
        if "Non" in imagename:
           print "**********{} has uid {}********".format(imagename, uid)
        setuid(image_obj, uid)
        set_dates(image_obj, data)
        image_obj.image = prep_image(
                                imagename=imagename,
                                data=image_data['data'],
                                content_type=image_data['content_type'],
                               )
        image_obj.reindexObject()
    else:
        print "image already present for {}".format(base_path)


def prep_image(imagename, data, content_type ):
        """ load image from data string """
        return NamedBlobImage(
                    data=b64decode(data),
                    contentType=str(content_type),
                    filename=unicode(imagename)
                    )
def prep_file(name, data, content_type ):
        """ load file from data string """
        return NamedBlobFile(
                    data=b64decode(data),
                    contentType=str(content_type),
                    filename=unicode(name)
                    )

def set_config(obj, data):
    pass
    if 'creation_date' in data:
        obj.setLayout(data['creation_date'])

def set_dates(obj, data):
    if 'creation_date' in data:
        obj.creation_date=data['creation_date']
    obj.setExpirationDate(data['expirationDate'])
    obj.setEffectiveDate(data['effectiveDate'])
    obj.setModificationDate(data['modification_date'])

def setuid(obj, uuid):
    """this sets uuid on dexterity content types
       see http://stackoverflow.com/questions/14955747/set-uid-for-dexterity-type
    """
    setattr(obj, ATTRIBUTE_NAME, uuid)

def prep_ExpirationDate(data):
    expiration_date = None
    if data["expirationDate"] not in ["None"]:
        expiration_date = DateTime(data["expirationDate"])
    return expiration_date
def changeWorkflowState(content, state_id, acquire_permissions=False,
                    portal_workflow=None, **kw):
    """
    from https://glenfant.wordpress.com/2010/04/02/changing-workflow-state-quickly-on-cmfplone-content/
    Change the workflow state of an object
    @param content: Content obj which state will be changed
    @param state_id: name of the state to put on content
    @param acquire_permissions: True->All permissions unchecked and on riles and
                                acquired
                                False->Applies new state security map
    @param portal_workflow: Provide workflow tool (optimisation) if known
    @param kw: change the values of same name of the state mapping
    @return: None
    """

    if portal_workflow is None:
        portal_workflow = getToolByName(content, 'portal_workflow')

    # Might raise IndexError if no workflow is associated to this type
    wf_def = portal_workflow.getWorkflowsFor(content)[0]
    wf_id= wf_def.getId()

    wf_state = {
        'action': None,
        'actor': None,
        'comments': "Setting state to %s" % state_id,
        'review_state': state_id,
        'time': DateTime(),
        }

    # Updating wf_state from keyword args
    for k in kw.keys():
        # Remove unknown items
        if not wf_state.has_key(k):
            del kw[k]
    if kw.has_key('review_state'):
        del kw['review_state']
    wf_state.update(kw)

    portal_workflow.setStatusOf(wf_id, content, wf_state)

    if acquire_permissions:
        # Acquire all permissions
        for permission in content.possible_permissions():
            content.manage_permission(permission, acquire=1)
    else:
        # Setting new state permissions
        wf_def.updateRoleMappingsFor(content)

    # Map changes to the catalogs
    content.reindexObject(idxs=['allowedRolesAndUsers', 'review_state'])

def prep_front_page():
    api.content.delete(obj=portal['front-page'])
    api.content.rename(obj=portal['front-pagezz'], new_id='front-page')
    portal.default_page = "front-page"
    frontpage = portal['front-page']
    frontpage.title = "Welcome to Our Site"
    frontpage.description = (
                    "This is our site ",
                    "We hope you like it., ",
                    "We think it's cool"
                    )
    frontpage.layout = "front-booking-view"

def inner_layouts():
    travel_info_layouts = [
         {'name':'legal','index':'legal-index'},
         {'name':'baggage','index':'free-baggage-allowance'},
         {'name':'optional-fees','index':'optional-fees'}
      ]
    portal['travel-info'].default_page = "optional-fees"
    for layout in travel_info_layouts:
        portal['travel-info'][layout['name']].default_page = layout['index']
    portal['ceos-message'].default_page = "ceos-message"
    portal.destinations.default_page = "aggregator"
    portal['destinations']['aggregator'].layout = "destinationListing"
    portal['tours'].default_page = "all-tours"
    portal['tours']["all-tours"].layout = "tours_gallery_view"
    portal['charters'].default_page = "charter-request-form"
    portal['cargo'].default_page = "cargo-form"
    portal['deals'].default_page = "aggregator"
    portal['deals']['aggregator'].layout = "deals_gallery_view"

    transaction.commit()

def clean_up():
    to_delete = ['footer',
                 'Members',
                 'carouselzzz',
                 'fly-clubzzzzz'
                 ]
    for deleteme in to_delete:
        print("... deleting {}".format(deleteme))
        api.content.delete(obj=portal[deleteme], check_linkintegrity=False)
    print("... make deals/aggregator public")
    api.content.transition(obj=portal['deals']['aggregator'],
                           transition='publish',
                           comment='Transition, initiated by import script'
                           )
    # Hide Home Page from Navigation Bar

    print("... removing home from the navbar")
    portal.portal_actions.portal_tabs.index_html.visible = False
    context = api.content.get(path="/")
    print("... removing portlets from right column")
    for name in ["news","events"]:
        removePortlet(
                context,
                name,
                columnName='plone.rightcolumn')
    transaction.commit()

def create_static_portlet(data):
    """ expects a data dictionary """
    portlet = static.Assignment(unicode(data['title']), unicode(data['text']))
    context = api.content.get(path=data['location']['path'])
    addPortlet(context, data['location']['portlet_manager'], portlet)

def import_zexps():
    zexps = [
     {'name':'cargo','target':'/'},
     {'name':'charters','target':'/'},
     {'name':'contact','target':'/'},
     {'name':'full-sponsorship','target':'/'},
     {'name':'sponsorship','target':'/'},
     {'name':'customer-relations-form','target':'/'}
     ]
    for zexp in zexps:
        context = api.content.get(path=zexp['target'])
        print("... importing {}".format(zexp['name']))
        importZEXP(context,zexp['name'])

def order_items():
    portal = api.portal.get()
    navbar_items = ['travel-info','destinations','tours','charters','cargo','contact']
    navbar_items.reverse()
    for item in navbar_items:
        portal.moveObjectsToTop([item])


def install_portlets():
    for portlet_file in portlet_files:
        with open(portlet_file) as portlet_data:
            data = yaml.load(portlet_data)
            create_static_portlet(data)

#return

IPSUM_LINE = "Lorem ipsum mel augue antiopam te. Invidunt constituto accommodare ius cu. Et cum solum liber doming, mel eu quem modus, sea probo putant ex."

IPSUM_PARAGRAPH = "<p>" + 10 * IPSUM_LINE + "</p>"




def getFile(module, *path):
    """return the file located in module.
    if module is None, treat path as absolut path
    path can be ['directories','and','file.txt'] or just 'file.txt'
    """
    modPath = ''
    if module:
        modPath = os.path.dirname(module.__file__)

    if type(path) == str:
        path = [path]
    filePath = os.path.join(modPath, *path)
    return file(filePath)

def getFileContent(module, *path):
    f = getFile(module, *path)
    data = safe_unicode(f.read())
    f.close()
    return data



def deleteItems(folder, *ids):
    """delete items in a folder and don't complain if they do not exist.
    """
    for itemId in ids:
        try:
            folder.manage_delObjects([itemId])
        except BadRequest:
            pass
        except AttributeError:
            pass

def todayPlusDays(nrDays=0, zopeDateTime=False):
    today = datetime.date.today()
    date = today + datetime.timedelta(days=nrDays)
    if zopeDateTime:
        return DateTime(date.isoformat())
    else:
        return date


def eventAndReindex(*objects):
    """fires an objectinitialized event and
    reindexes the object(s) after creation so it can be found in the catalog
    """
    for obj in objects:
        event.notify(ObjectInitializedEvent(obj))
        obj.reindexObject()



def workflowAds(home, wfdefs):
    """
    do workflow transitions and set enddate to datetime if set.

    sample format
    wfdefs = [('plone-dev', ['publish'], None),
              ('minimal-job', ['submit'], datetime),
              ('plone-dev', ['publish']),
              ]
    """


    wft = getToolByName(home, 'portal_workflow')

    for id, actions, date in wfdefs:
        ad = home.unrestrictedTraverse(id)
        for action in actions:
            wft.doActionFor(ad, action)
        if date:
            ad.expirationDate = date
        ad.reindexObject(idxs=['end', 'review_state'])



def removePortlet(context, portletName, columnName='plone.leftcolumn'):
    manager = getUtility(IPortletManager, columnName)
    assignmentMapping = getMultiAdapter((context, manager), IPortletAssignmentMapping)
    # throws a keyerror if the portlet does not exist
    del assignmentMapping[portletName]

def blockPortlets(context, columnName='plone.leftcolumn', inherited=None, group=None, contenttype=None):
    """True will block portlets, False will show them, None will skip settings.
    """

    manager = getUtility(IPortletManager, name=columnName)
    assignable = getMultiAdapter((context, manager), ILocalPortletAssignmentManager)

    if group is not None:
        assignable.setBlacklistStatus(GROUP_CATEGORY, group)
    if contenttype is not None:
        assignable.setBlacklistStatus(CONTENT_TYPE_CATEGORY, contenttype)
    if inherited is not None:
        assignable.setBlacklistStatus(CONTEXT_CATEGORY, inherited)


def hidePortlet(context, portletName, columnName='plone.leftcolumn'):
    manager = getUtility(IPortletManager, columnName)
    assignmentMapping = getMultiAdapter((context, manager), IPortletAssignmentMapping)
    settings = IPortletAssignmentSettings(assignmentMapping[portletName])
    settings['visible'] = False



def hasPortlet(context, portletName, columnName='plone.leftcolumn'):
    manager = getUtility(IPortletManager, columnName)
    assignmentMapping = getMultiAdapter((context, manager), IPortletAssignmentMapping)
    return assignmentMapping.has_key(portletName)

def setPortletWeight(portlet, weight):
    """if collective weightedportlets can be imported
    we do set the weight, and do not do anything otherwise
    """
    try:
        from collective.weightedportlets import ATTR
        from persistent.dict import PersistentDict
        if not hasattr(portlet, ATTR):
            setattr(portlet, ATTR, PersistentDict())
        getattr(portlet, ATTR)['weight'] = weight
    except ImportError:
        #simply don't do anything in here
        pass






def createImage(context, id, file, title='', description=''):
    """create an image and return the object
    """
    context.invokeFactory('Image', id, title=title,
                          description=description)
    context[id].setImage(file)
    return context[id]

def createFile(context, id, file, title='', description=''):
    context.invokeFactory('File', id, title=title,
                          description=description)
    context[id].setFile(file)
    return context[id]

def excludeFromNavigation(obj, exclude=True):
    """excludes the given obj from navigation
    make sure to reindex the object afterwards to make the
    navigation portlet notice the change
    """

    obj._md['excludeFromNav'] = exclude

def getRelativePortalPath(context):
    """return the path of the plonesite
    """
    url = getToolByName(context, 'portal_url')
    return url.getPortalPath()

def getRelativeContentPath(obj):
    """return the path of the object
    """
    url = getToolByName(obj, 'portal_url')
    return '/'.join(url.getRelativeContentPath(obj))


def doWorkflowTransition(obj, transition):
    """to the workflow transition on the specified object
    we don't use wft.doActionFor directly since this does not set the effective
    data
    """

    doWorkflowTransitions([obj], transition)


def doWorkflowTransitions(objects=[], transition='publish', includeChildren=False):
    """use this to publish a/some folder(s) optionally including their child elements
    """

    if not objects:
        return
    if type(objects) != ListType:
        objects = [objects, ]

    utils = getToolByName(objects[0], 'plone_utils')
    for obj in objects:
        path = '/'.join(obj.getPhysicalPath())
        utils.transitionObjectsByPaths(workflow_action=transition, paths=[path], include_children=includeChildren)


def constrainTypes(obj, allowed=[], notImmediate=[]):
    """sets allowed and immediately addable types for obj.

    to only allow news and images and make both immediately addable use::

       constrainTypes(portal.newsfolder, ['News Item', 'Image'])

    if images should not be immediately addable you would use::

       constrainTypes(portal.newsfolder, ['News Item', 'Image'], notImmediate=['Image'])
    """

    obj.setConstrainTypesMode(1)
    obj.setLocallyAllowedTypes(allowed)

    if notImmediate:
        immediate = [type for type in allowed if type not in notImmediate]
    else:
        immediate = allowed
    obj.setImmediatelyAddableTypes(immediate)


#################################
# This is where we do stuff
##################################
# create_folders(level=1)
# import_data_levels
#
# create_folders(level=2)
# transaction.commit()
#
# create_folders(level=3)
# transaction.commit()

print("----------> -- Importing zexps")
import_zexps()
print("----------> Starting site import of {} site".format(site_id))
print("----------> Preparing data from json files")
data = get_level(json_files)
import_data_levels(data)
print("----------> Importing data")
print("----------> Running Post Import Tasks")
print("----------> -- Setting front page to use front-booking-view")
prep_front_page()
print("----------> -- Setting inner layouts")
inner_layouts()
print("----------> -- Cleaning up old items (footer ...)")
clean_up()
print("----------> -- Assigning Portlets")
install_portlets()
order_items()
transaction.commit()



# --------
