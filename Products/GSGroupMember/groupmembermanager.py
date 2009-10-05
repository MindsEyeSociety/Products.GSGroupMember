# coding=utf-8
from zope.interface.interface import Interface
from zope.component import createObject
from zope.interface import implements, Attribute
from zope.formlib import form
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import sort_by_name

from groupMembersInfo import GSGroupMembersInfo
from groupmemberactions import GSMemberStatusActions
from interfaces import IGSGroupMemberManager, IGSMemberActionsSchema

class GSGroupMemberManager(object):
    implements(IGSGroupMemberManager)
    
    def __init__(self, group):
        self.context = group
        
        self.siteInfo = createObject('groupserver.SiteInfo', group)
        self.groupInfo = createObject('groupserver.GroupInfo', group)
        self.membersInfo = GSGroupMembersInfo(group)
        
        self.__memberStatusActions = None
        self.__form_fields = None
    
    @property
    def memberStatusActions(self):
        if self.__memberStatusActions == None:
            self.__memberStatusActions = \
              [ GSMemberStatusActions(m, 
                  self.groupInfo, self.siteInfo)
                for m in self.membersInfo.members ]
        return self.__memberStatusActions
    
    @property
    def form_fields(self):
        if self.__form_fields == None:
            fields = \
              form.Fields(IGSMemberActionsSchema)
            for m in self.memberStatusActions:
                f = m.form_fields
                fields = \
                  form.Fields(
                    fields
                    +
                    form.Fields(f)
                  )
            self.__form_fields = fields.omit('dummy')
        return self.__form_fields
    
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
        
        SIDE EFFECTS
            Resets the self.__form_fields cache.
        '''
        assert type(newData) == dict        
        oldData = self.get_data()
        # Change stuff.
        # Reset the self.__form_fields cache, as 
        # the data keys will have changed.
    data = property(get_data, set_data)
