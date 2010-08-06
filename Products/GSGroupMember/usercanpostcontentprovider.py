# coding=utf-8
from zope.component import createObject, provideAdapter, adapts
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.contentprovider.interfaces import IContentProvider, \
  UpdateNotCalled
from zope.interface import Interface, implements
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from Products.GSGroup.joining import GSGroupJoining

from interfaces import IGSUserCanPostContentProvider
from groupmembership import JoinableGroupsForSite, InvitationGroupsForSite

import logging
log = logging.getLogger('GSUserCanPostContentProvider') #@UndefinedVariable

class GSUserCanPostContentProvider(object):
    """GroupServer context-menu for the user profile area.
    """

    implements(IGSUserCanPostContentProvider)
    adapts(Interface,
        IDefaultBrowserLayer,
        Interface)

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
            raise UpdateNotCalled

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
        joinableGroups = JoinableGroupsForSite(self.userInfo.user)
        retval = self.groupInfo.id in joinableGroups
        assert type(retval) == bool
        return retval
    
    @property   
    def canInvite(self):
        invitationGroups = InvitationGroupsForSite(self.userInfo.user,
                                               self.groupInfo.groupObj)
        retval = (self.groupInfo.id in invitationGroups) and \
          not self.canJoin
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
        return GSGroupJoining(self.groupInfo.groupObj).joinability
        
provideAdapter(GSUserCanPostContentProvider,
               provides=IContentProvider,
               name="groupserver.UserCanPost")

