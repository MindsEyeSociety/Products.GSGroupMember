# coding=utf-8
from zope.component import createObject
from zope.interface import implements
from Products.XWFCore.XWFUtils import sort_by_name

from groupmembership import GroupMembers, InvitedGroupMembers
from interfaces import IGSGroupMembersInfo

class GSGroupMembersInfo(object):
    implements(IGSGroupMembersInfo)
    
    def __init__(self, group):
        self.context = group

        self.siteInfo = createObject('groupserver.SiteInfo', group)
        self.groupInfo = createObject('groupserver.GroupInfo', group)

        self.__members = None
        self.__fullMembers = None
        self.__fullMemberCount = None
        self.__invitedMembers = None
        self.__invitedMemberCount = None
        
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
            allMembers = self.fullMembers + self.invitedMembers
            fullMemberIds = set([m.id for m in self.fullMembers])
            invitedMemberIds = set([m.id for m in self.invitedMembers])
            distinctMemberIds = fullMemberIds.union(invitedMemberIds)
            members = []
            for uId in distinctMemberIds:
                member = [m for m in allMembers if m.id==uId][0]
                members.append(member)
            members.sort(sort_by_name)
            self.__members = members
        return self.__members

