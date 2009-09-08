# coding=utf-8
from zope.contentprovider import tales
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.app.pagetemplate import ViewPageTemplateFile, metaconfigure
from zope.component import createObject, provideAdapter, adapts
from zope.interface import implements, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.contentprovider.interfaces import UpdateNotCalled, IContentProvider

from interfaces import IGSMemberStatusActionsContentProvider

class GSMemberStatusActionsContentProvider(object):
    '''Display a group member\'s status and actions to take'''
    implements( IGSMemberStatusActionsContentProvider )
    adapts(Interface, IDefaultBrowserLayer, Interface)

    def __init__(self, context, request, view):
        self.__parent__ = self.view = view
        self.__updated = False
    
        self.context = context
        self.request = request
        
    def update(self):
        try:
            metaconfigure.registerType('provider', 
              tales.TALESProviderExpression)
        except Exception, e:
            print '***Registration of "provider" failed: %s***' % e
            pass
        self.__updated = True
            
    def render(self):
        if not self.__updated:
            raise UpdateNotCalled
        pageTemplate = ViewPageTemplateFile(self.pageTemplateFileName)
        retval = pageTemplate(self,
                              view=self)
        return retval
    

provideAdapter(GSMemberStatusActionsContentProvider,
    provides=IContentProvider,
    name='groupserver.MemberStatusActions')

