# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.interfaces import IGSUserInfo

from groupmembershipstatus import GSGroupMembershipStatus
from groupmembership import GroupMembers

import logging
log = logging.getLogger('GSGroupMember')

class GSManageGroupMembers(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', self.context)
        self.groupInfo = createObject('groupserver.GroupInfo', self.context)

        self.__groupMembers = None
        self.__memberCount = None
        self.__statuses = None 

    @property
    def groupMembers(self):
        if self.__groupMembers == None:
            self.__groupMembers = GroupMembers(self.context)
        return self.__groupMembers
    
    @property
    def memberCount(self):
        if self.__memberCount == None:
            self.__memberCount = len(self.groupMembers)
        return self.__memberCount
    
    @property
    def statuses(self):
        if self.__statuses == None:
            self.__statuses = \
                [ GSGroupMembershipStatus(m, self.groupInfo) 
                  for m in self.groupMembers.members ]
        return self.__statuses
    
    