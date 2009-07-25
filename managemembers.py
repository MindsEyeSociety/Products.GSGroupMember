# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import sort_by_name

from groupmembershipstatus import GSGroupMembershipStatus
from groupmembership import GroupMembers, InvitedGroupMembers

import logging
log = logging.getLogger('GSGroupMember')

class GSManageGroupMembers(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)

        self.__members = None
        self.__fullMembers = None
        self.__fullMemberCount = None
        self.__invitedMembers = None
        self.__invitedMemberCount = None
        self.__statuses = None 
        
    @property
    def fullMembers(self):
        if self.__fullMembers == None:
            self.__fullMembers = \
              GroupMembers(self.context).members
        return self.__fullMembers
    
    @property
    def fullMemberCount(self):
        if self.__fullMemberCount == None:
            self.__fullMemberCount = \
              len(self.fullMembers)
        return self.__fullMemberCount
    
    @property
    def invitedMembers(self):
        if self.__invitedMembers == None:
            self.__invitedMembers = \
              InvitedGroupMembers(self.context, self.siteInfo).members
        return self.__invitedMembers
    
    @property
    def invitedMemberCount(self):
        if self.__invitedMemberCount == None:
            self.__invitedMemberCount = \
              len(self.invitedMembers)
        return self.__invitedMemberCount
    
    @property
    def members(self):
        if self.__members == None:
            members = \
              self.fullMembers + self.invitedMembers
            members.sort(sort_by_name)
            self.__members = members
        return self.__members
    
    @property
    def statuses(self):
        if self.__statuses == None:
            self.__statuses = \
              [ GSGroupMembershipStatus(m, self.groupInfo, self.siteInfo)
                for m in self.members ]
        return self.__statuses
