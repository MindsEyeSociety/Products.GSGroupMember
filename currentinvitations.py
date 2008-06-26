# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.userinfo import GSUserInfo
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSGroupMember')

class GSCurrentInviations(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.userInfo = GSUserInfo(context)
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

    @property
    def currentInvitations(self):
        retval = self.groupMemberQuery.get_current_invitiations(
         self.siteInfo.id, self.userInfo.id)
        assert type(retval) == list
        return retval

