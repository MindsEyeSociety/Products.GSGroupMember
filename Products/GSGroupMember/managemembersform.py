# coding=utf-8
from Products.Five.formlib.formbase import PageForm
from zope.component import createObject
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from groupmembermanager import GSGroupMemberManager
from interfaces import IGSManageGroupMembersForm

class GSManageGroupMembersForm(PageForm):
    pageTemplateFileName = 'browser/templates/manage_members.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
        
    def __init__(self, context, request):
        PageForm.__init__(self, context, request)
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.groupName = self.groupInfo.name
        self.label = 'Manage the Members of %s' % self.groupName

        self.memberManager = GSGroupMemberManager(self.groupInfo.groupObj)
        self.form_fields = self.memberManager.form_fields
    
    def setUpWidgets(self, ignore_request=False, data=None):
        self.adapters = {}
        if not data:
            data = self.memberManager.data
        self.widgets = form.setUpWidgets(
            self.form_fields, self.prefix, self.context,
            self.request, form=self, data=data,
            ignore_request=ignore_request)
        assert self.widgets
        
    @form.action(label=u'Change', failure='handle_change_action_failure')
    def handle_change(self, action, data):
        self.status = u'Something changed!'
        #assert data
#        assert self.memberManager
#        self.memberManager.data = data

    def handle_change_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'
        
        
