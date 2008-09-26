# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.GSGroupMember.groupmembership import GroupMembers

import logging
log = logging.getLogger('GSGroupMember')

class GSManageGroupMembers(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.group_members = GroupMembers(context).members

