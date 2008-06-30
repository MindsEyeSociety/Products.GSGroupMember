# coding=utf-8
from Products.Five.formlib.formbase import PageForm
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.formlib import form
from zope.component import createObject
from Products.CustomUserFolder.interfaces import ICustomUser, IGSUserInfo
from Products.GSProfile.edit_profile import multi_check_box_widget
from interfaces import IGSInvitationGroups

import logging
log = logging.getLogger('GSInviteUser')

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

        self.form_fields['invitation_groups'].custom_widget =\
          multi_check_box_widget
        
    @form.action(label=u'Invite', failure='handle_invite_action_failure')
    def handle_invite(self, action, data):
        self.status = u'Fii'
        
    def handle_invite_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

