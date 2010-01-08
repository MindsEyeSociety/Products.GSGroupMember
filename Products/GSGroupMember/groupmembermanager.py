# coding=utf-8
from zope.component import createObject
from zope.interface import implements
from zope.formlib import form

from Products.XWFCore.odict import ODict
from Products.XWFCore.XWFUtils import comma_comma_and
from Products.GSGroup.mailinglistinfo import GSMailingListInfo
from Products.GSGroup.changebasicprivacy import radio_widget

from Products.GSGroupMember.memberstatusaudit import StatusAuditor, GAIN, LOSE
from Products.GSGroupMember.groupMembersInfo import GSGroupMembersInfo
from Products.GSGroupMember.groupmemberactions import GSMemberStatusActions
from Products.GSGroupMember.interfaces import IGSGroupMemberManager, IGSMemberActionsSchema, IGSManageMembersForm

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
        ptnCoachToRemove = data.pop('ptnCoachRemove')
        toChange = filter(lambda k:data.get(k), data.keys())
        
        # Sanity check before doing things on a per-user basis.
        ptnCoachToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'ptnCoach' ]
        if ptnCoachToAdd:
            assert len(ptnCoachToAdd)==1, \
              'More than one user specified as the '\
              'Participation Coach for %s: %s' %\
              (self.groupInfo.id, ptnCoachToAdd)
        
        # Aggregate actions to take by user.
        actions = ODict()
        for k in toChange:
            memberId = k.split('-')[0]
            if not actions.has_key(memberId):
                actions[memberId] = k.split('-')[1]
            else:
                actions[memberId] =\
                  actions[memberId].append(k.split('-')[1])
        retval = self.set_data(ptnCoachToRemove, actions)
        
        # Reset the caches so that we get the member
        # data afresh when the form reloads.
        self.__membersInfo = None
        self.__memberStatusActions = None
        self.__form_fields = None
        return retval
                
    def set_data(self, ptnCoachToRemove, changes):
        retval = ''''''
        
        if ptnCoachToRemove:
            retval = self.removePtnCoach()
        
        for memberId in changes.keys():
            userInfo = \
                    createObject('groupserver.UserFromId', 
                      self.group, memberId)
            auditor = StatusAuditor(self.group, userInfo)
            actions = changes[memberId]
            if 'remove' in actions:
                retval += self.removeMember(memberId)
                continue
            if 'ptnCoach' in actions:
                retval += self.addPtnCoach(memberId, auditor)
            if 'groupAdminAdd' in actions:
                retval += self.addAdmin(memberId, auditor)
            if 'groupAdminRemove' in actions:
                retval += self.removeAdmin(memberId, auditor)
            if 'moderatorAdd' in actions:
                retval += self.addModerator(memberId, auditor)
            if 'moderatorRemove' in actions:
                retval += self.removeModerator(memberId, auditor)
            if 'moderatedAdd' in actions:
                retval += self.moderate(memberId, auditor) 
            if 'moderatedRemove' in actions:
                retval += self.unmoderate(memberId, auditor)
            if 'postingMemberAdd' in actions:
                retval += self.addPostingMember(memberId, auditor)
            if 'postingMemberRemove' in actions:
                retval += self.removePostingMember(memberId, auditor)
        return retval
        
    def removePtnCoach(self):
        retval = ''
        oldPtnCoach = self.groupInfo.ptn_coach
        if self.group.hasProperty('ptn_coach_id'):
            self.group.manage_changeProperties(ptn_coach_id='')
        if self.listInfo.mlist.hasProperty('ptn_coach_id'):
            self.listInfo.mlist.manage_changeProperties(ptn_coach_id='')
        if oldPtnCoach:
            auditor = StatusAuditor(self.group, oldPtnCoach)
            auditor.info(LOSE, 'Participation Coach')
            retval = '<p><a href="%s">%s</a> is no longer the Participation Coach.</p>' % \
              (oldPtnCoach.url, oldPtnCoach.name)
        return retval
        
    def addPtnCoach(self, ptnCoachToAdd, auditor):
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
        auditor.info(GAIN, 'Participation Coach')
        retval += '<p><a href="%s">%s</a> is now the Participation Coach.</p>' %\
         (newPtnCoach.url, newPtnCoach.name)
        return retval
    
    def addAdmin(self, userId, auditor):
        self.group.manage_addLocalRoles(userId, ['GroupAdmin'])
        auditor.info(GAIN, 'Group Administrator')
        admin = createObject('groupserver.UserFromId', self.group, userId)
        retval = '<p><a href="%s">%s</a> is now a Group Administrator.</p>' %\
         (admin.url, admin.name)
        return retval

    def removeAdmin(self, userId, auditor):
        roles = list(self.group.get_local_roles_for_userid(userId))
        try:
            roles.remove('GroupAdmin')
        except:
            pass
        if roles:
            self.group.manage_setLocalRoles(userId, roles)
        else:
            self.group.manage_delLocalRoles([userId])
        auditor.info(LOSE, 'Group Administrator')
        admin = createObject('groupserver.UserFromId', self.group, userId)
        retval = '<p><a href="%s">%s</a> is no longer a Group Administrator.</p>' %\
         (admin.url, admin.name)
        return retval
    
    def addModerator(self, userId, auditor):
        retval = ''
        return retval
        
    def removeModerator(self, userId, auditor):
        retval = ''
        return retval
        
    def moderate(self, userId, auditor):
        retval = ''
        return retval
        
    def unmoderate(self, userId, auditor):
        retval = ''
        return retval
        
    def addPostingMember(self, userId, auditor):
        retval = ''
        return retval
        
    def removePostingMember(self, userId, auditor):
        retval = ''
        return retval
        
    def removeMember(self, userId):
        retval = ''
        return retval
        