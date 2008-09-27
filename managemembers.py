# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSGroupMember.groupmembership import GroupMembers
from Products.GSGroupMember.groupmembershipstatus import GSGroupMembershipStatus

import logging
log = logging.getLogger('GSGroupMember')

class GSManageGroupMembers(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', self.context)
        self.groupInfo = createObject('groupserver.GroupInfo', self.context)

        self.group_members = GroupMembers(self.context)
        self.member_count = len(self.group_members)
        self.statuses = [ GSGroupMembershipStatus(m, self.groupInfo) 
                            for m in self.group_members.members ]

