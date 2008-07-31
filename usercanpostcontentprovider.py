from zope.component import createObject
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 
from Products.XWFCore import XWFUtils, ODict
from Products.CustomUserFolder.interfaces import IGSUserInfo
from interfaces import *
from groupmembership import JoinableGroupsForSite, InvitationGroupsForSite

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
        self.groupsInfo = createObject('groupserver.GroupsInfo', 
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
    
    @property
    def ptnCoach(self):
        ptnCoachId = self.groupInfo.get_property('ptn_coach_id')
        retval = createObject('groupserver.UserFromId',
          self.context, ptnCoachId)
        return retval 

    @property
    def canJoin(self):
        joinableGroups = JoinableGroupsForSite(self.userInfo.user,
                                               self.groupInfo.groupObj)
        retval = self.groupInfo.id in joinableGroups
        assert type(retval) == bool
        return retval
    
    @property   
    def canInvite(self):
        invitationGroups = InvitationGroupsForSite(self.userInfo.user,
                                               self.groupInfo.groupObj)
        retval = self.groupInfo.id in invitationGroups
        assert type(retval) == bool
        return retval

    @property
    def loginUrl(self):
        assert self.request
        assert self.request.URL
        retval = '/login.html?came_from=%s' % self.request.URL
        assert retval
        return retval
        
    @property
    def joinability(self):
        return GSGroupJoining(self.groupInfo.groupObj).joinability()
        
zope.component.provideAdapter(GSUserCanPostContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.UserCanPost")

