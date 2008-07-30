from zope.component import createObject
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 
from Products.XWFCore import XWFUtils, ODict
from Products.CustomUserFolder.interfaces import IGSUserInfo
from interfaces import *

import logging
log = logging.getLogger('GSUserCanPostContentProvider')

class GSUserCanPostContentProvider(object):
    """GroupServer context-menu for the user profile area.
    """

    zope.interface.implements( IGSUserCanPostContentProvider )
    zope.component.adapts(zope.interface.Interface,
        zope.publisher.interfaces.browser.IDefaultBrowserLayer,
        zope.interface.Interface)

    def __init__(self, context, request, view):
        self.__parent__ = self.view = view
        self.__updated = False

        self.context = context
        self.request = request
        
    def update(self):
        self.__updated = True

        self.siteInfo = createObject('groupserver.SiteInfo', 
          self.context)
        self.groupInfo = createObject('groupserver.GroupInfo', 
          self.context)
        self.userInfo = createObject('groupserver.LoggedInUser', 
          self.context)

    def render(self):
        if not self.__updated:
            raise interfaces.UpdateNotCalled

        pageTemplate = PageTemplateFile(self.pageTemplateFileName)
        return pageTemplate(view=self)
        
    #########################################
    # Non standard methods below this point #
    #########################################

zope.component.provideAdapter(GSUserCanPostContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.UserCanPost")

