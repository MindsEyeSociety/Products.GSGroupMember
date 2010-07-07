# coding=utf-8
try:
    from five.formlib.formbase import PageForm
except ImportError:
    from Products.Five.formlib.formbase import PageForm

from zope.component import createObject
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Products.GSProfile.edit_profile import multi_check_box_widget
from Products.GSGroup.changebasicprivacy import radio_widget
from interfaces import IGSInviteSiteMembers
from groupmembership import invite_to_groups

import logging
log = logging.getLogger('GSInviteSiteMembersForm') #@UndefinedVariable

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

        self.form_fields['site_members'].custom_widget = \
          multi_check_box_widget
        self.form_fields['delivery'].custom_widget = radio_widget

    # --=mpj17=--
    # The "form.action" decorator creates an action instance, with
    #   "handle_invite" set to the success handler,
    #   "handle_invite_action_failure" as the failure handler, and adds the
    #   action to the "actions" instance variable (creating it if 
    #   necessary).
    @form.action(label=u'Invite', failure='handle_invite_action_failure')
    def handle_invite(self, action, data):
        adminInfo = createObject('groupserver.LoggedInUser', self.context)

        for userId in data['site_members']:
            userInfo = createObject('groupserver.UserFromId',
                                    self.context, userId)

            invite_to_groups(userInfo, adminInfo, self.groupInfo)
            msg = u'<li><a class="fn" href="%s">%s</a></li>' %\
              (userInfo.url, userInfo.name)
            self.status = '%s\n%s' % (self.status, msg)

            if data['delivery'] == 'email':
                # --=mpj17=-- The default is one email per post
                pass
            elif data['delivery'] == 'digest':
                userInfo.user.set_enableDigestByKey(self.groupInfo.id)
            elif data['delivery'] == 'web':
                userInfo.user.set_disableDeliveryByKey(self.groupInfo.id)

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

