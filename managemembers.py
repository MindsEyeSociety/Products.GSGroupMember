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

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.group_members = GroupMembers(context).members
        self.statuses = [ GSGroupMembershipStatus(m, self.groupInfo) 
                            for m in self.group_members ]

