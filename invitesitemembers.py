# coding=utf-8
import time, md5
from Products.Five.formlib.formbase import PageForm
from zope.component import createObject, adapts
from zope.interface import implements, providedBy, implementedBy,\
  directlyProvidedBy, alsoProvides
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.app.form.browser import MultiCheckBoxWidget, SelectWidget,\
  TextAreaWidget
from zope.security.interfaces import Forbidden
from zope.app.apidoc.interface import getFieldsInOrder
import AccessControl

from Products.CustomUserFolder.interfaces import ICustomUser, IGSUserInfo
from Products.GSProfile.edit_profile import multi_check_box_widget
from interfaces import IGSInviteSiteMembers
from queries import GroupMemberQuery
from utils import invite_id

import logging
log = logging.getLogger('GSInviteSiteMembersForm')

class GSInviteSiteMembersForm(PageForm):
    label = u'Invite Site Members'
    pageTemplateFileName = 'browser/templates/invitesitemembers.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSInviteSiteMembers, render_context=False)

    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.context = context
        self.request = request
        
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo= createObject('groupserver.GroupInfo', context)
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

        self.form_fields['site_members'].custom_widget = \
          multi_check_box_widget

    # --=mpj17=--
    # The "form.action" decorator creates an action instance, with
    #   "handle_invite" set to the success handler,
    #   "handle_invite_action_failure" as the failure handler, and adds the
    #   action to the "actions" instance variable (creating it if 
    #   necessary).
    @form.action(label=u'Invite', failure='handle_invite_action_failure')
    def handle_invite(self, action, data):
        viewingUser = AccessControl.getSecurityManager().getUser()
        viewingUserInfo = createObject('groupserver.UserFromId', 
          self.context, viewingUser.getId())
        for userId in data['site_members']:
            userInfo = createObject('groupserver.UserFromId',
                                    self.context, userId)

            inviteId = invite_id(self.siteInfo.id, self.groupInfo.id,
                                 userInfo.id, viewingUserInfo.id)

            self.groupMemberQuery.add_invitation(inviteId, 
              self.siteInfo.id, self.groupInfo.id, userInfo.id, 
              viewingUserInfo.id)
              
            responseURL = '%s/r/group_invitation/%s' % (self.siteInfo.url, 
                                                        inviteId)
            n_dict={'userFn': userInfo.name,
                    'invitingUserFn': viewingUserInfo.name,
                    'siteName': self.siteInfo.name,
                    'siteURL': self.siteInfo.url,
                    'groupName': self.groupInfo.name,
                    'responseURL': responseURL}
            userInfo.user.send_notification('invite_join_group', 'default',
              n_dict=n_dict)

            m = u'%s (%s) inviting %s (%s) to join %s (%s) on %s (%s) with id %s'%\
              (viewingUserInfo.name, viewingUserInfo.id,
               userInfo.name, userInfo.id,
               self.groupInfo.name, self.groupInfo.id,
               self.siteInfo.name, self.siteInfo.id,
               inviteId)
            log.info(m)

            msg = u'<li><a class="fn" href="%s">%s</a></li>' %\
              (userInfo.url, userInfo.name)
            self.status = '%s\n%s' % (self.status, msg)
        self.status = u'<p>Invited the following users to '\
          u'join <a class="fn" href="%s">%s</a></p><ul>%s</ul>' %\
            (self.groupInfo.url, self.groupInfo.name, self.status)

        if not(data['site_members']):
            self.status = u'<p>No site members were selected.</p>'
        assert self.status
        assert type(self.status) == unicode

    def handle_invite_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'



