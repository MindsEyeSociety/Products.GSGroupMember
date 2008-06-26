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

    @property
    def pastInvitations(self):
        m = u'Generating a list of current past group-invitations for '\
          u'%s (%s) on %s (%s).' %\
            (self.userInfo.name, self.userInfo.id,
             self.siteInfo.name, self.siteInfo.id)
        log.info(m)
        
        invitations = self.groupMemberQuery.get_past_invitiations_for_site(
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

        
    @property
    def sentInvitations(self):
        invitations = self.groupMemberQuery.get_invitations_sent_by_user(
            self.siteInfo.id, self.userInfo.id)
        for inv in invitations:
            usrInf = createObject('groupserver.UserFromId', 
              self.context, inv['user_id'])
            inv['user'] = usrInf
            grpInf = createObject('groupserver.GroupInfo', 
              self.context, inv['group_id'])
            inv['group'] = grpInf
        assert type(invitations) == list
        return invitations

    def get_response(self, accepted):
        retval = u'Declined'
        if accepted:
            retval = u'Accepted'
        assert type(retval) == unicode
        assert retval in (u'Declined', u'Accepted')
        return retval

