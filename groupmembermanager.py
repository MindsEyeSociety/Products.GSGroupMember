# coding=utf-8
from zope.component import createObject
from zope.interface import implements
from zope.formlib import form
from zope.schema import TextLine
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import sort_by_name

from groupMembersInfo import GSGroupMembersInfo
from interfaces import IGSGroupMemberManager

class GSGroupMemberManager(object):
    implements(IGSGroupMemberManager)
    
    def __init__(self, group):
        self.context = group

        self.siteInfo = createObject('groupserver.SiteInfo', group)
        self.groupInfo = createObject('groupserver.GroupInfo', group)
        self.membersInfo = GSGroupMembersInfo(group)

        self.__memberStatusActions = None
        #self.__form_fields = None
        self.form_fields = form.Fields(
          form.Fields(TextLine(__name__='foo',
            title=u'Foo',
            description=u'A placeholder widget',
            required=False)
          )
        )
    
    def get_data(self):
        '''Get the membership data.
        
        DESCRIPTION
            Get the membership data to be displayed as form widgets
            for updating the status of members within the group.
        
        RETURNS
            A dict. The keys match the IDs of the attributes in the
            manage members form, so it can be used for setting the 
            values in the form.
        '''
        retval = {}
        assert type(retval) == dict
        return retval

    def set_data(self, newData):
        '''Set the membership data
        
        DESCRIPTION
            Updates the status of members within the group.
            
        ARGUMENTS
            A dict. The keys must match the IDs of the attributes in
            the manage members form (which should not be too hard, as 
            this is done automatically by Formlib).  
        '''
        assert type(newData) == dict        
        oldData = self.get_data()
        # Change stuff.
    data = property(get_data, set_data)
