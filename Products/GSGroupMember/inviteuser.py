# coding=utf-8
try:
    from five.formlib.formbase import PageForm
except ImportError:
    from Products.Five.formlib.formbase import PageForm
from zope.component import createObject
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSProfile.edit_profile import multi_check_box_widget

from interfaces import IGSInvitationGroups
from groupmembership import invite_to_groups

import logging
log = logging.getLogger('GSInviteUserForm') #@UndefinedVariable

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
        viewingUserInfo = createObject('groupserver.LoggedInUser', 
          self.context)

        self.status = u''
        
        gso = self.groupsInfo.groupsObj
        groups = [createObject('groupserver.GroupInfo', gso, gid) 
                  for gid in data['invitation_groups']]
        invite_to_groups(self.userInfo, viewingUserInfo, groups)

        gn = ['<a href="%s">%s</a>' %(g.url, g.name) for g in groups]
        if len(gn) > 1:
            c = u', '.join(gn[:-1])
            g = u' and '.join((c, gn[-1]))
        else:
            g = gn[0]
            
        self.status = u'<p>Invited <a class="fn" href="%s">%s</a> to '\
          u'join %s</p>' %\
            (self.userInfo.url, self.userInfo.name, g)
        assert type(self.status) == unicode
        
    def handle_invite_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

