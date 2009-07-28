# coding=utf-8
from zope.component import createObject
from zope.interface import implements
from zope.formlib import form
from zope.schema import TextLine
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import sort_by_name

from groupmembershipstatus import GSGroupMembershipStatus
from groupmembership import GroupMembers, InvitedGroupMembers
from interfaces import IGSManageGroupMembers

class GSManageGroupMembers(object):
    implements(IGSManageGroupMembers)
    
    def __init__(self, group):
        self.context = group

        self.siteInfo = createObject('groupserver.SiteInfo', group)
        self.groupInfo = createObject('groupserver.GroupInfo', group)

        self.__members = None
        self.__fullMembers = None
        self.__fullMemberCount = None
        self.__invitedMembers = None
        self.__invitedMemberCount = None
        self.__statuses = None
        self.form_fields = form.Fields(
          form.Fields(TextLine(__name__='foo',
            title=u'Foo',
            description=u'A placeholder widget',
            required=False)
          )
        )
        
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
