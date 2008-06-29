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

    def process_form(self):
        '''Process the forms in the page.
        
        This method uses the "submitted" pattern that is used for the
        XForms impementation on GroupServer. 
          * The method is called whenever the page is loaded by
            tal:define="result view/process_form".
          * The submitted form is checked for the hidden "submitted" field.
            This field is only returned if the user submitted the form,
            not when the page is loaded for the first time.
            - If the field is present, then the form is processed.
            - If the field is absent, then the method re  turns.
        
        RETURNS
            A "result" dictionary, that at-least contains the form that
            was submitted
        '''
        form = self.context.REQUEST.form
        result = {}
        result['form'] = form

        if form.has_key('submitted'):
            groupIds = [k.split('-respond')[0] for k in form.keys() 
              if  '-respond' in k]
            responses = [form['%s-respond' % k] for k in groupIds]          

            result['error'] = False            
            m = u''

            accepted = [k.split('-accept')[0] for k in responses
              if '-accept' in k]
            if accepted:
                acceptedGroups = [createObject('groupserver.GroupInfo',
                  self.groupsInfo.groupsObj, g) for g in accepted]
                am = ', '.join(['%s (%s)' % (g.name, g.id) 
                                for g in acceptedGroups])
                lm = u'%s (%s) accepting invitations to join the groups '\
                  u'%s on %s (%s)' % (self.userInfo.name, self.userInfo.id,
                  am, self.siteInfo.name, self.siteInfo.id)
                log.info(lm)

                self.accept_invitations(accepted)
                
                acceptedLinks = ['<a href="%s">%s</a>' % (g.url, g.name)
                  for g in acceptedGroups]
                if len(acceptedLinks) > 1:
                    c = u', '.join([g for g in acceptedLinks][:-1])
                    a = u' and '.join((c, acceptedLinks[-1]))
                    i = 'invitations'
                    t = 'these groups'
                else:
                    a = acceptedLinks[0]
                    i = 'invitation'
                    t = 'this group'
                m = u'Accepted the %s to join %s. You are now a member of '\
                  u'%s.' % (i, a, t)
            else:
                m = u'You did not accept any invitations.'
                
            declined = [k.split('-decline')[0] for k in responses
              if '-decline' in k]
            for d in declined:
                assert d not in accepted
            if declined:
                declinedGroups = [createObject('groupserver.GroupInfo',
                  self.groupsInfo.groupsObj, g) for g in declined]
                dm = ', '.join(['%s (%s)' % (g.name, g.id) 
                                for g in declinedGroups])
                lm = u'%s (%s) declining invitations to join the groups '\
                  u'%s on %s (%s)' % (self.userInfo.name, self.userInfo.id,
                  dm, self.siteInfo.name, self.siteInfo.id)
                log.info(lm)
                
                self.decline_invitations(declined)
                
                declinedLinks = ['<a href="%s">%s</a>' % (g.url, g.name)
                  for g in declinedGroups]
                if len(declinedLinks) > 1:
                    c = u', '.join([g for g in declinedLinks][:-1])
                    a = u' and '.join((c, declinedLinks[-1]))
                    i = 'invitations'
                else:
                    a = declinedLinks[0]
                    i = 'invitation'
                m = u'<ul><li>%s</li>'\
                  u'<li>Declined the %s to join %s.</li</ul>' %\
                  (m, i, a)
            else:
               m = u'<ul><li>%s</li>'\
                  u'<li>You did not decline any invitations.</li</ul>' % m

            result['message'] = m
            self.__currentInvitations = None            
    
            assert result.has_key('error')
            assert type(result['error']) == bool
            assert result.has_key('message')
            assert type(result['message']) == unicode
        
        assert result.has_key('form')
        assert type(result['form']) == dict
        return result

    def accept_invitations(self, groupIds):
        '''Accept the invitations to the groups
        
        DESCRIPTION
          Accept the invitations to a list of groups, joining the groups.
            
        ARGUMENTS
          "groupIds": A list of group-identifiers
            
        RETURNS
          None
            
        SIDE EFFECTS
          The current user ("self.context") is joined to the groups. The
          invitations are marked as accepted, and the current date is
          put down as the response-date.
        '''
        assert type(groupIds) == list
        
        inviteIds = [i['group_id'] for i in self.currentInvitations]
        accept_invite = self.groupMemberQuery.accept_invitation
        for gid in groupIds:
            assert gid in inviteIds, 'Not invited to %s' % gid
            memberGroup = '%s_member' % gid
            self.context.add_groupWithNotification(memberGroup)
            accept_invite(self.siteInfo.id, gid, self.userInfo.id)

    def decline_invitations(self, groupIds):
        '''
        DESCRIPTION
        
        ARGUMENTS
        
        RETURNS
        
        SIDE EFFECTS
        '''
        inviteIds = [i['group_id'] for i in self.currentInvitations]
        for gid in groupIds:
            assert gid in self.currentInvitations, 'Not invited to %s' % gid

        di = self.groupMemberQuery.decline_invitation
        for gid in groupIds:
            di(self.siteInfo.id, gid, self.userInfo.id)

