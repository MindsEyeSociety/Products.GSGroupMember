# coding=utf-8
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
from Products.XWFCore import XWFUtils
from interfaceCoreProfile import *
from Products.CustomUserFolder.interfaces import ICustomUser, IGSUserInfo

class GSEditImageForm(PageForm):
    label = u'Invite Site Members'
    pageTemplateFileName = 'browser/templates/invitesitemembers.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSInviteSiteMembers, render_context=False)

    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo= createObject('groupserver.GroupInfo', context)
        
    # --=mpj17=--
    # The "form.action" decorator creates an action instance, with
    #   "handle_invite" set to the success handler,
    #   "handle_invite_action_failure" as the failure handler, and adds the
    #   action to the "actions" instance variable (creating it if 
    #   necessary).
    @form.action(label=u'Invite', failure='handle_invite_action_failure')
    def handle_invite(self, action, data):
        self.status = u"No fields changed."
        assert self.status
        assert type(self.status) == unicode

    def handle_invite_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'



