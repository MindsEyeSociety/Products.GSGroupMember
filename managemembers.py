# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSGroup.queries import GroupQuery

from groupmembershipstatus import GSGroupMembershipStatus
from groupmembership import GroupMembers

import logging
log = logging.getLogger('GSGroupMember')

class GSManageGroupMembers(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)

        self.gq = GroupQuery(context, context.zsqlalchemy)
        assert self.gq

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
              [ GSGroupMembershipStatus(m, self.groupInfo)
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
            invitations = \
              self.gq.get_current_invitations_for_group(self.siteInfo.id, 
                                                        self.groupInfo.id)
            self.__invitedMembers = \
              [ createObject('groupserver.UserFromId', 
                  self.context, i['user_id']) 
                for i in invitations ]
        return self.__invitedMembers
    
    @property
    def invitedMembersStatuses(self):
        if self.__invitedMembersStatuses == None:
            statuses = []
            for m in self.invitedMembers:
                status = GSGroupMembershipStatus(m, self.groupInfo)
                status.isInvited = True
                statuses.append(status)
            self.__invitedMembersStatuses = statuses
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
