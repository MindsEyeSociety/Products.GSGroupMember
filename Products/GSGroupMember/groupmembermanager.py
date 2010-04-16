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

import logging
log = logging.getLogger('GSGroupMemberManager')

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

        # Members to remove. If selected for removal,
        #  the JS should stop any other actions being
        #  specified for that member, but let's not
        #  make any assumptions.
        membersToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'remove' ]
        for k in toChange:
            if k.split('-')[0] in membersToRemove:
                toChange.remove(k)
        
        # Posting members to remove.
        postingMembersToRemove = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'postingMemberRemove' ]
        
        # Sanity check re number of ptn coaches,
        #  and establishing whether the current
        #  one needs to be removed even if that
        #  was not explicitly required.
        ptnCoachToAdd = \
          [ k.split('-')[0] for k in toChange 
            if k.split('-')[1] == 'ptnCoach' ]
        if ptnCoachToAdd:
            assert len(ptnCoachToAdd)==1, \
              'More than one user specified as the '\
              'Participation Coach for %s: %s' %\
              (self.groupInfo.id, ptnCoachToAdd)
            if self.groupInfo.ptn_coach:
                ptnCoachToRemove = True
        
        # Aggregate other actions to take by user.
        otherActions = ODict()
        for k in toChange:
            memberId = k.split('-')[0]
            if not otherActions.has_key(memberId):
                otherActions[memberId] = k.split('-')[1]
            else:
                otherActions[memberId] =\
                  otherActions[memberId].append(k.split('-')[1])
        retval = self.set_data(membersToRemove, ptnCoachToRemove, otherActions)
        
        # Reset the caches so that we get the member
        # data afresh when the form reloads.
        self.__membersInfo = None
        self.__memberStatusActions = None
        self.__form_fields = None
        return retval
                
    def set_data(self, membersToRemove, postingMembersToRemove, ptnCoachToRemove, changes):
        retval = ''''''
        changeLog = ODict()

        # 1. Remove all the members to be removed.
        for memberId in membersToRemove:
            changeLog[memberId] = self.removeMember(memberId)
        
        # 2. Remove all the posting members to be removed.
        for memberId in postingMembersToRemove:
            changeLog[memberId] = [self.removePostingMember(memberId)]
        
        # 3. If there's a ptn coach to be removed, do it now.
        if ptnCoachToRemove:
            oldCoachId, change = self.removePtnCoach()
            if oldCoachId:
                if not changeLog.has_key(memberId):
                    changeLog[oldCoachId] = [change]
                else:
                    changeLog[oldCoachId] += [change]
        
        # 4. Make other changes member by member.
        for memberId in changes.keys():
            userInfo = \
              createObject('groupserver.UserFromId', 
                self.group, memberId)
            auditor = StatusAuditor(self.group, userInfo)
            actions = changes[memberId]
            if not changeLog.has_key(memberId):
                changeLog[memberId] = []
            if 'ptnCoach' in actions:
                retval += self.addPtnCoach(memberId, auditor)
            if 'groupAdminAdd' in actions:
                retval += self.addAdmin(memberId, auditor)
            if 'groupAdminRemove' in actions:
                retval += self.removeAdmin(memberId, auditor)
            if 'moderatorAdd' in actions:
                retval += self.addModerator(userInfo.user, auditor)
            if 'moderatorRemove' in actions:
                retval += self.removeModerator(memberId, auditor)
            if 'moderatedAdd' in actions:
                retval += self.moderate(memberId, auditor) 
            if 'moderatedRemove' in actions:
                retval += self.unmoderate(memberId, auditor)
            if 'postingMemberAdd' in actions:
                retval += self.addPostingMember(memberId, auditor)
            retval += '<ul><label><a href="%s">%s</a> has undergone '\
              'the following changes:</label>'
            for change in changeLog[memberId]:
                retval += '<li>%s</li>' % change
            retval += '</ul>'
        return retval
        
    def addPtnCoach(self, ptnCoachToAdd, auditor):
        # The old Participation Coach should have been removed
        # after we set removePtnCoach to True after doing our
        # sanity check in make_changes().
        # We'll call it again to be safe, and check whether it
        # was necessary. But if so, we'll just log it and carry on. 
        if self.removePtnCoach():
            msg = 'Participation Coach should have been '\
              'removed before setting new one, but wasn\'t.'
            log.warn(msg)
        if self.group.hasProperty('ptn_coach_id'):
            self.group.manage_changeProperties(ptn_coach_id=ptnCoachToAdd)
        else:
            self.group.manage_addProperty('ptn_coach_id', ptnCoachToAdd, 'string')

        if self.listInfo.mlist.hasProperty('ptn_coach_id'):
            self.listInfo.mlist.manage_changeProperties(ptn_coach_id=ptnCoachToAdd)
        else:
            self.listInfo.mlist.manage_addProperty('ptn_coach_id', ptnCoachToAdd, 'string')
        auditor.info(GAIN, 'Participation Coach')
        retval = 'Became the Participation Coach.'
        return retval
    
    def addAdmin(self, userId, auditor):
        self.group.manage_addLocalRoles(userId, ['GroupAdmin'])
        auditor.info(GAIN, 'Group Administrator')
        retval = 'Became a Group Administrator.'
        return retval

    def removeAdmin(self, userId, auditor):
        roles = list(self.group.get_local_roles_for_userid(userId))
        assert 'GroupAdmin' in roles
        roles.remove('GroupAdmin')
        if roles:
            self.group.manage_setLocalRoles(userId, roles)
        else:
            self.group.manage_delLocalRoles([userId])
        auditor.info(LOSE, 'Group Administrator')
        retval = 'No longer a Group Administrator.'
        return retval
    
    def addModerator(self, userId, auditor):
        moderatorIds = self.listInfo.mlist.getProperty('moderator_members', [])
        assert userId not in moderatorIds
        moderatorIds.append(userId)
        
        if self.listInfo.mlist.hasProperty('moderator_members'):
            self.listInfo.mlist.manage_changeProperties(moderator_members=moderatorIds)
        else:
            self.listInfo.mlist.manage_addProperty('moderator_members', moderatorIds, 'lines')

        auditor.info(GAIN, 'Moderator')
        retval = 'Became a Moderator.'
        return retval
        
    def removeModerator(self, userId, auditor):
        moderatorIds = self.listInfo.mlist.getProperty('moderator_members', [])
        assert userId in moderatorIds
        moderatorIds.remove(userId)
        
        if self.listInfo.mlist.hasProperty('moderator_members'):
            self.listInfo.mlist.manage_changeProperties(moderator_members=moderatorIds)
        else:
            self.listInfo.mlist.manage_addProperty('moderator_members', moderatorIds, 'lines')

        auditor.info(LOSE, 'Moderator')
        retval = 'No longer a Moderator.'
        return retval
        
    def moderate(self, userId, auditor):
        moderatedIds = self.listInfo.mlist.getProperty('moderated_members', [])
        assert userId not in moderatedIds
        moderatedIds.append(userId)
        
        if self.listInfo.mlist.hasProperty('moderated_members'):
            self.listInfo.mlist.manage_changeProperties(moderated_members=moderatedIds)
        else:
            self.listInfo.mlist.manage_addProperty('moderated_members', moderatedIds, 'lines')

        auditor.info(GAIN, 'Moderated')
        retval = 'Became Moderated.'
        return retval
        
    def unmoderate(self, userId, auditor):
        moderatedIds = self.listInfo.mlist.getProperty('moderated_members', [])
        assert userId in moderatedIds
        moderatedIds.remove(userId)
        
        if self.listInfo.mlist.hasProperty('moderated_members'):
            self.listInfo.mlist.manage_changeProperties(moderated_members=moderatedIds)
        else:
            self.listInfo.mlist.manage_addProperty('moderated_members', moderatedIds, 'lines')

        auditor.info(LOSE, 'Moderated')
        retval = 'No longer Moderated.'
        
    def addPostingMember(self, userId, auditor):
        postingMemberIds = self.listInfo.mlist.getProperty('posting_members', [])
        
        numPostingMembers = len(postingMemberIds)
        if ((numPostingMembers >= 5) or (numPostingMembers+len(userids) > 5)):
            haveOrHas = ((len(userids) > 1) and 'have') or 'has'
            result['error'] = True
            result['message'] = '''%s %s not been added to the list of posting
             members, as it would put the number of posting members beyond the
             maximum (five).''' % (userNames, haveOrHas)
            return result
           
           
        if member not in postingMemberIds:
            self.listInfo.mlist.append(member)
        
        if grouplist.hasProperty('posting_members'):
            grouplist.manage_changeProperties(posting_members=postingMembers)
        else:
            grouplist.manage_addProperty('posting_members', postingMembers, 'lines')
        
        retval = ''
        return retval
    
    def removePtnCoach(self):
        retval = ('','')
        oldPtnCoach = self.groupInfo.ptn_coach
        if self.group.hasProperty('ptn_coach_id'):
            self.group.manage_changeProperties(ptn_coach_id='')
        if self.listInfo.mlist.hasProperty('ptn_coach_id'):
            self.listInfo.mlist.manage_changeProperties(ptn_coach_id='')
        if oldPtnCoach:
            auditor = StatusAuditor(self.group, oldPtnCoach)
            auditor.info(LOSE, 'Participation Coach')
            retval = (oldPtnCoach.id, 'No longer the Participation Coach.')
        return retval
            
    def removePostingMember(self, userId):
        postingMemberIds = self.listInfo.mlist.getProperty('posting_members', [])
        assert userId in postingMemberIds
        postingMemberIds.remove(userId)
        
        if self.listInfo.mlist.hasProperty('posting_members'):
            self.listInfo.mlist.manage_changeProperties(posting_members=postingMemberIds)
        else:
            self.listInfo.mlist.manage_addProperty('posting_members', postingMemberIds, 'lines')

        userInfo = createObject('groupserver.UserFromId', 
                    self.group, memberId)
        auditor = StatusAuditor(self.group, userInfo)
        auditor.info(LOSE, 'Posting Member')
        retval = 'No longer a Posting Member.'
        return retval
        
    def removeMember(self, userId):
        changes = []
        oldPtnCoach = self.groupInfo.ptn_coach
        if oldPtnCoach and (oldPtnCoach.id==userId):
            changes.append(self.removePtnCoach()[1])
        changes.append(self.removeAdmin(userId, auditor))
        changes.append(self.removePostingMember(userId, auditor))
        changes.append(self.removeModerator(userId, auditor))
        changes.append(self.unmoderate(userId, auditor))
        # Actually remove from group.
        userInfo = createObject('groupserver.UserFromId', 
                    self.group, memberId)
        auditor = StatusAuditor(self.group, userInfo)
        # Audit removal from group.
        retval = filter(None, changes)
        return retval
        