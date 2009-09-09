# coding=utf-8
from Products.Five.formlib.formbase import PageForm
from zope.component import createObject
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.GSGroup.changebasicprivacy import radio_widget
from interfaces import IGSJoinGroup
from groupmembership import join_group

class JoinForm(PageForm):
    label = u'Join'
    pageTemplateFileName = 'browser/templates/join.pt'
    template = ZopeTwoPageTemplateFile(pageTemplateFileName)
    form_fields = form.Fields(IGSJoinGroup, render_context=False)

    def __init__(self, context, request):
        PageForm.__init__(self, context, request)

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)

        self.form_fields['delivery'].custom_widget = radio_widget
        
        self.__userInfo = None
        
    @property
    def userInfo(self):
        if self.__userInfo == None:
            self.__userInfo = createObject('groupserver.LoggedInUser',
              self.context)
        return self.__userInfo
        
    @form.action(label=u'Join', failure='handle_join_action_failure')
    def handle_invite(self, action, data):

        join_group(self.userInfo.user, self.groupInfo)

        if data['delivery'] == 'email':
            # --=mpj17=-- The default is one email per post
            m = u'You will receive one email message per post.'
        elif data['delivery'] == 'digest':
            self.userInfo.user.set_enableDigestByKey(self.groupInfo.id)
            m = u'You will receive a daily digest of topics.'
        elif data['delivery'] == 'web':
            self.userInfo.user.set_disableDeliveryByKey(self.groupInfo.id)
            m = 'You will not receive any email from this group.'

        self.status = u'You have joined <a class="group" href="%s">%s</a>. %s' %\
          (self.groupInfo.url, self.groupInfo.name, m)
        assert type(self.status) == unicode
        
    def handle_join_action_failure(self, action, data, errors):
        if len(errors) == 1:
            self.status = u'<p>There is an error:</p>'
        else:
            self.status = u'<p>There are errors:</p>'

