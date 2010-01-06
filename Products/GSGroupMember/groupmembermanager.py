# coding=utf-8
from zope.component import createObject
from zope.interface import implements
from zope.formlib import form

from Products.XWFCore.XWFUtils import comma_comma_and
from Products.GSGroup.mailinglistinfo import GSMailingListInfo
from Products.GSGroup.changebasicprivacy import radio_widget

from groupMembersInfo import GSGroupMembersInfo
from groupmemberactions import GSMemberStatusActions
from interfaces import IGSGroupMemberManager, IGSMemberActionsSchema, IGSManageMembersForm

class GSGroupMemberManager(object):
    implements(IGSGroupMemberManager)
    
    def __init__(self, group):
        self.group = group
        
        self.siteInfo = createObject('groupserver.SiteInfo', group)
        self.groupInfo = createObject('groupserver.GroupInfo', group)
        self.listInfo = GSMailingListInfo(group)
        
        self.__membersInfo = self.__memberStatusActions = None
        self.__form_fields = None
    
    @property
    def membersInfo(self):
        if self.__membersInfo == None:
            self.__membersInfo = GSGroupMembersInfo(self.group)
        return self.__membersInfo
    
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
              form.Fields(IGSManageMembersForm)
            for m in self.memberStatusActions:
                fields = \
                  form.Fields(
                    fields
                    +
                    form.Fields(m.form_fields)
                  )
            fields['ptnCoachRemove'].custom_widget = radio_widget
            self.__form_fields = fields
        return self.__form_fields

    def make_changes(self, data):
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
        retval = ''''''

        ptnCoachToRemove = data.pop('ptnCoachRemove')
        if ptnCoachToRemove:
            retval += self.removePtnCoach()
        toChange = filter(lambda k:data.get(k), data.keys())
        
        adminsToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'groupAdminAdd' ]
        retval += self.addAdmins(adminsToAdd)
        adminsToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'groupAdminRemove' ]
        retval += self.removeAdmins(adminsToRemove)

        ptnCoachToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'ptnCoach' ]
        retval += self.addPtnCoach(ptnCoachToAdd)

        moderatorsToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'moderatorAdd' ]
        self.addModerators(moderatorsToAdd)
        moderatorsToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'moderatorRemove' ]
        self.removeModerators(moderatorsToRemove)
        
        moderatedToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'moderatedAdd' ]
        self.addModerated(moderatedToAdd)
        moderatedToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'moderatedRemove' ]
        self.removeModerated(moderatedToRemove)
        
        postingToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'postingMemberAdd' ]
        self.addPostingMembers(postingToAdd)
        postingToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'postingMemberRemove' ]
        self.removePostingMembers(postingToRemove)
        
        membersToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'remove' ]
        self.removeMembers(membersToRemove)

        # Reset the caches so that we get the member
        # data afresh when the form reloads.
        self.__membersInfo = None
        self.__memberStatusActions = None
        self.__form_fields = None
        return retval
    
    def addAdmins(self, userIds):
        retval = u''
        #for userId in userIds:
        #    self.group.manage_addLocalRoles(userId, ['GroupAdmin'])
        if userIds:
            userNames = \
              comma_comma_and([ createObject('groupserver.UserFromId', 
                                  self.group, userId).name 
                                for userId in userIds])
            m = (len(userIds) == 1) and ('member you selected (%s) has' % userNames) \
              or ('%d members you selected (%s) have' % (len(userIds), userNames))
            retval = '<p>The %s been given Group Administrator status.</p>' % m
        return retval

    def removeAdmins(self, userIds):
        retval = u''
        #for userId in userIds:
        #    roles = list(self.group.get_local_roles_for_userid(userId))
        #    try:
        #        roles.remove('GroupAdmin')
        #    except:
        #        pass
        #    if roles:
        #        self.group.manage_setLocalRoles(userId, roles)
        #    else:
        #        self.group.manage_delLocalRoles([userId])
        if userIds:
            userNames = \
              comma_comma_and([ createObject('groupserver.UserFromId', 
                                  self.group, userId).name 
                                for userId in userIds])
            m = (len(userIds) == 1) and ('member you selected (%s) has' % userNames) \
              or ('%d members you selected (%s) have' % (len(userIds), userNames))
            retval = '<p>The %s had Group Administrator status revoked.</p>' % m
        return retval
    
    def addPtnCoach(self, userIds):
        retval = ''
        if userIds:
            assert len(userIds)==1, 'More than one user '\
              'specified to be the participation coach: %s' % userIds
            ptnCoachToAdd = userIds[0]
            retval = self.removePtnCoach()
            if self.group.hasProperty('ptn_coach_id'):
                self.group.manage_changeProperties(ptn_coach_id=ptnCoachToAdd)
            else:
                self.group.manage_addProperty('ptn_coach_id', ptnCoachToAdd, 'string')
    
            if self.listInfo.mlist.hasProperty('ptn_coach_id'):
                self.listInfo.mlist.manage_changeProperties(ptn_coach_id=ptnCoachToAdd)
            else:
                self.listInfo.mlist.manage_addProperty('ptn_coach_id', ptnCoachToAdd, 'string')
            newPtnCoach = createObject('groupserver.UserFromId', self.group, 
                                          ptnCoachToAdd)
            retval += '<p><a href="%s">%s</a> is now the Participation Coach.</p>' %\
             (newPtnCoach.url, newPtnCoach.name)
        return retval 
    
    def removePtnCoach(self):
        retval = ''
        oldPtnCoach = self.groupInfo.ptn_coach
        if self.group.hasProperty('ptn_coach_id'):
            self.group.manage_changeProperties(ptn_coach_id='')
        if self.listInfo.mlist.hasProperty('ptn_coach_id'):
            self.listInfo.mlist.manage_changeProperties(ptn_coach_id='')
        if oldPtnCoach:
            retval = '<p><a href="%s">%s</a> is no longer the Participation Coach.</p>' % \
              (oldPtnCoach.url, oldPtnCoach.name)
        return retval
    
    def addModerators(self, userIds):
        if userIds:
            return userIds
        
    def removeModerators(self, userIds):
        if userIds:
            return userIds
        
    def addModerated(self, userIds):
        if userIds:
            return userIds
        
    def removeModerated(self, userIds):
        if userIds:
            return userIds
        
    def addPostingMembers(self, userIds):
        if userIds:
            return userIds
        
    def removePostingMembers(self, userIds):
        if userIds:
            return userIds
        
    def removeMembers(self, userIds):
        if userIds:
            return userIds
        