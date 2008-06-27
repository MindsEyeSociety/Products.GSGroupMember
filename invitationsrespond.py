# coding=utf-8
from Products.Five import BrowserView
from zope.component import createObject
from Products.CustomUserFolder.userinfo import GSUserInfo
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSGroupMember')

class GSInviationsRespond(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.userInfo = GSUserInfo(context)
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)
        
        self.__currentInvitations = None
        self.__pastInvitations = None

    @property
    def currentInvitations(self):
        if self.__currentInvitations == None:
            self.__currentInvitations = self.get_currentInvitations()
        assert type(self.__currentInvitations) == list
        return self.__currentInvitations
        
    def get_currentInvitations(self):
        m = u'Generating a list of current group-invitations for %s (%s) '\
          u'on %s (%s).' %\
            (self.userInfo.name, self.userInfo.id,
             self.siteInfo.name, self.siteInfo.id)
        log.info(m)
        
        invitations = self.groupMemberQuery.get_current_invitiations_for_site(
            self.siteInfo.id, self.userInfo.id)
        for inv in invitations:
            usrInf = createObject('groupserver.UserFromId', 
              self.context, inv['inviting_user_id'])
            inv['inviting_user'] = usrInf
            grpInf = createObject('groupserver.GroupInfo',
              self.groupsInfo.groupsObj, inv['group_id'])
            inv['group'] = grpInf
            
        assert type(invitations) == list
        return invitations

