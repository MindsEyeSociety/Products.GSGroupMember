# coding=utf-8
import time, md5
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.formlib import form
from zope.component import createObject
import AccessControl
from Products.CustomUserFolder.interfaces import ICustomUser, IGSUserInfo
from Products.GSProfile.edit_profile import multi_check_box_widget
from Products.XWFCore.XWFUtils import convert_int2b62
from interfaces import IGSInvitationGroups
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSInviteUserForm')

class InviteUserForm(PageForm):
    label = u'Invite User'
    pageTemplateFileName = 'browser/templates/inviteuser.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSInvitationGroups, render_context=False)

    def __init__(self, context, request):
        PageForm.__init__(self, context, request)

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.userInfo = IGSUserInfo(context)

        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

        self.form_fields['invitation_groups'].custom_widget =\
          multi_check_box_widget
        
    @form.action(label=u'Invite', failure='handle_invite_action_failure')
    def handle_invite(self, action, data):
        viewingUser = AccessControl.getSecurityManager().getUser()
        viewingUserInfo = createObject('groupserver.UserFromId', 
          self.context, viewingUser.getId())

        self.status = u''
        for gid in data['invitation_groups']:
            istr = time.asctime() + self.siteInfo.id +\
              gid + self.userInfo.id + viewingUserInfo.id
            inum = long(md5.new(istr).hexdigest(), 16)
            inviteId = str(convert_int2b62(inum))
            groupInfo = createObject('groupserver.GroupInfo', 
              self.groupsInfo.groupsObj, gid)

            self.groupMemberQuery.add_invitation(inviteId, 
              self.siteInfo.id, gid, self.userInfo.id, 
              viewingUserInfo.id)

            m = u'%s (%s) inviting %s (%s) to join %s (%s) on %s (%s) with id %s'%\
              (viewingUserInfo.name, viewingUserInfo.id,
               self.userInfo.name, self.userInfo.id,
               groupInfo.name, groupInfo.id,
               self.siteInfo.name, self.siteInfo.id,
               inviteId)
            log.info(m)

            msg = u'<li><a class="group" href="%s">%s</a></li>' %\
              (groupInfo.url, groupInfo.name)
            self.status = '%s\n%s' % (self.status, msg)
        self.status = u'<p>Invited <a class="fn" href="%s">%s</a> to '\
          u'join</p><ul>%s</ul>' %\
            (self.userInfo.url, self.userInfo.name, self.status)
        assert type(self.status) == unicode
        
    def handle_invite_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

