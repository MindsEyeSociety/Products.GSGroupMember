# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.interfaces import IGSUserInfo

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

        self.__verifiedGroupMembers = None
        self.__verifiedGroupMembersStatuses = None
        self.__verifiedMemberCount = None
        self.__invitedMembers = None
        self.__invitedMembersStatuses = None
        self.__invitedMemberCount = None
        self.__statuses = None 
        self.__memberCount = None
        
    @property
    def verifiedGroupMembers(self):
        if self.__verifiedGroupMembers == None:
            self.__verifiedGroupMembers = GroupMembers(self.context).members
        return self.__verifiedGroupMembers
    
    @property
    def verifiedGroupMembersStatuses(self):
        if self.__verifiedGroupMembersStatuses == None:
            self.__verifiedGroupMembersStatuses =\
              [ GSGroupMembershipStatus(m, self.groupInfo, self.siteInfo)
                for m in self.verifiedGroupMembers ]
        return self.__verifiedGroupMembersStatuses
    
    @property
    def verifiedMemberCount(self):
        if self.__verifiedMemberCount == None:
            self.__verifiedMemberCount = len(self.verifiedGroupMembersStatuses)
        return self.__verifiedMemberCount
    
    @property
    def invitedMembers(self):
        if self.__invitedMembers == None:
            self.__invitedMembers = \
              InvitedGroupMembers(self.context, self.siteInfo).members
        return self.__invitedMembers
    
    @property
    def invitedMembersStatuses(self):
        if self.__invitedMembersStatuses == None:
            self.__invitedMembersStatuses = \
              [ GSGroupMembershipStatus(m, self.groupInfo, self.siteInfo)
                for m in self.invitedMembers ]
        return self.__invitedMembersStatuses
    
    @property
    def invitedMemberCount(self):
        if self.__invitedMemberCount == None:
            self.__invitedMemberCount = \
              len(self.invitedMembersStatuses)
        return self.__invitedMemberCount
    
    @property
    def statuses(self):
        if self.__statuses == None:
            self.__statuses = \
              self.verifiedGroupMembersStatuses \
              + \
              self.invitedMembersStatuses
        return self.__statuses
