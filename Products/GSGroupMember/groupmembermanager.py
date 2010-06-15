# coding=utf-8
from AccessControl import getSecurityManager
from zope.component import createObject
from zope.interface import implements
from zope.formlib import form

from Products.XWFCore.odict import ODict
from Products.XWFCore.XWFUtils import comma_comma_and, getOption
from Products.GSGroup.mailinglistinfo import GSMailingListInfo
from Products.GSGroup.changebasicprivacy import radio_widget

from Products.GSGroupMember.leaveaudit import LeaveAuditor, REMOVE
from Products.GSGroupMember.memberstatusaudit import StatusAuditor, GAIN, LOSE
from Products.GSGroupMember.groupMembersInfo import GSGroupMembersInfo
from Products.GSGroupMember.groupmemberactions import GSMemberStatusActions
from Products.GSGroupMember.interfaces import IGSGroupMemberManager
from Products.GSGroupMember.interfaces import IGSMemberActionsSchema, IGSManageMembersForm

import logging
log = logging.getLogger('GSGroupMemberManager')

MAX_POSTING_MEMBERS = 5

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
        if ptnCoachToRemove:
            toChange['ptnCoachToRemove'] = True
        changes, cancelled = self.marshallChanges(toChange)
        retval = self.set_data(changes, cancelled)
        
        # Reset the caches so that we get the member
        # data afresh when the form reloads.
        self.__membersInfo = None
        self.__memberStatusActions = None
        self.__form_fields = None
        return retval

    def marshallChanges(self, toChange):
        retval = {}
        for k in toChange:
            memberId, action = k.split('-')
            if retval.has_key(action):
                retval[action].append(memberId)
            else:
                retval[action] = [memberId]
        toChange, cancelledChanges = self.sanitiseChanges(retval)
        retval = (self.changesByUser(toChange), cancelledChanges)
        return retval
    
    def sanitiseChanges(self, toChange):
        cancelledChanges = {}
        actions = toChange.keys()
        
        # For members to be removed, cancel all other actions.
        #  Don't bother reporting on these cancellations.
        for mId in toChange.get('remove',[]):
            for a in filter(lambda x:(x!='remove') and (x!='ptnCoachToRemove'), actions):
                members = toChange.get(a,[])
                if mId in members:
                    members.remove(mId)
                    toChange[a] = members
        
        # Check if a member to be removed is also the Ptn Coach, and update removal if req'd.
        if self.groupInfo.ptn_coach and (self.groupInfo.ptn_coach in toChange.get('remove',[])):
            toChange['ptnCoachToRemove'] = True
        
        # If more than one ptnCoach was specified, then cancel the change.
        ptnCoachToAdd = toChange.get('ptnCoach',[])
        if ptnCoachToAdd and (len(ptnCoachToAdd)>1):
            cancelledChanges['ptnCoach'] = ptnCoachToAdd
            toChange.pop('ptnCoach')
        elif len(ptnCoachToAdd)==1:
            toChange['ptnCoach'] = ptnCoachToAdd[0]
            if self.groupInfo.ptn_coach:   # Update Ptn Coach removal if req'd.
                toChange['ptnCoachToRemove'] = True
        
        # Check for double moderation.
        toBeModerated = toChange.get('moderatedAdd',[])
        toBeModerators = toChange.get('moderatorAdd',[])
        cancelledChanges['doubleModeration'] = \
          [ mId for mId in toBeModerators if mId in toBeModerated ]
        for mId in cancelledChanges['doubleModeration']:
            toBeModerated.remove(mId)
            toBeModerators.remove(mId)
        if toBeModerated:
            toChange['moderatedAdd'] = toBeModerated
        else:
            toChange.pop('moderatedAdd')
        if toBeModerators:
            toChange['moderatorAdd'] = toBeModerators
        else:
            toChange.pop('moderatorAdd')
        
        retval = (toChange, cancelledChanges)
        return retval

    def changesByUser(self, toChange):
        retval = {}
        for k in toChange.keys():
            mIds = toChange[k]
            for mId in mIds:
                if retval.has_key(mId):
                    retval[mId] = retval[mId].append(k)
                else:
                    retval[mId] = [k]
        return retval 

    def set_data(self, changes, notTaken):
        retval = ''''''
        changeLog = ODict()
        
        # 0. Summarise actions not taken.
        if notTaken.has_key('ptnCoach'):
            attemptedChangeIds = notTaken['ptnCoach']
            attemptedChangeUsers = \
              [ createObject('groupserver.UserFromId', self.group, a)
                for a in attemptedChangeIds ]
            attemptedNames = [a.name for a in attemptedChangeUsers ]
            retval += '<p>The Participation Coach was <b>not changed</b>, '\
              'because there can be only one and you specified %d (%s).</p>' %\
              (len(attemptedChangeIds), comma_comma_and(attemptedNames))
        if notTaken.has_key('doubleModeration'):
            attemptedChangeIds = notTaken['doubleModeration']
            attemptedChangeUsers = \
              [ createObject('groupserver.UserFromId', self.group, a)
                for a in attemptedChangeIds ]
            memberMembers = len(attemptedChangeIds)==1 and 'member was' or 'members were'
            retval += '<p>The moderation level of the following %s '\
              '<b>not changed</b>, because members cannot be both ' \
              'moderated and moderators:</p><ul>' % memberMembers
            for m in attemptedChangeUsers:
                retval += '<li><a href="%s">%s</a></li>' %\
                  (m.url, m.name)
            retval += '</ul>'

        # 1. Remove all the members to be removed.
        for memberId in changes.get('remove',[]):
            changeLog[memberId] = self.removeMember(memberId)
        
        # 2. Remove all the posting members to be removed.
        for memberId in changes.get('postingMemberRemove',[]):
            changeLog[memberId] = [self.removePostingMember(memberId)]
        
        # 3. If there's a ptn coach to be removed, do it now.
        if changes.get('ptnCoachToRemove', False):
            oldCoachId, change = self.removePtnCoach()
            if oldCoachId:
                if not changeLog.has_key(oldCoachId):
                    changeLog[oldCoachId] = [change]
                else:
                    changeLog[oldCoachId].append(change)
        
        # 4. If there's a ptn coach to add, do it now.
        ptnCoachToAdd = changes.get('ptnCoach',[])
        if ptnCoachToAdd:
            change = self.addPtnCoach(ptnCoachToAdd)
            if not changeLog.has_key(ptnCoachToAdd):
                changeLog[ptnCoachToAdd] = [change]
            else:
                changeLog[ptnCoachToAdd].append(change)
        
        # 5. Make other changes member by member.
        for memberId in changes.keys():
            userInfo = \
              createObject('groupserver.UserFromId', 
                self.group, memberId)
            auditor = StatusAuditor(self.group, userInfo)
            actions = changes[memberId]
            if not changeLog.has_key(memberId):
                changeLog[memberId] = []
            if 'groupAdminAdd' in actions:
                changeLog[memberId].append(self.addAdmin(memberId, auditor))
            if 'groupAdminRemove' in actions:
                changeLog[memberId].append(self.removeAdmin(memberId, auditor))
            if 'moderatorAdd' in actions:
                changeLog[memberId].append(self.addModerator(memberId, auditor))
            if 'moderatorRemove' in actions:
                changeLog[memberId].append(self.removeModerator(memberId, auditor))
            if 'moderatedAdd' in actions:
                changeLog[memberId].append(self.moderate(memberId, auditor))
            if 'moderatedRemove' in actions:
                changeLog[memberId].append(self.unmoderate(memberId, auditor))
            if 'postingMemberAdd' in actions:
                changeLog[memberId].append(self.addPostingMember(memberId, auditor))

        # 5. Format the feedback.
        for memberId in changeLog.keys():
            userInfo = \
              createObject('groupserver.UserFromId', 
                self.group, memberId)
            retval += '<p><a href="%s">%s</a> has undergone '\
              'the following changes:</p><ul>' % (userInfo.url, userInfo.name)
            for change in changeLog[memberId]:
                retval += '<li>%s</li>' % change
            retval += '</ul>'
        return retval
        
    def addAdmin(self, userId, auditor):
        roles = list(self.group.get_local_roles_for_userid(userId))
        assert 'GroupAdmin' not in roles, '%s was marked for becoming '\
          'a GroupAdmin in %s (%s), but is one already.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        self.group.manage_addLocalRoles(userId, ['GroupAdmin'])
        auditor.info(GAIN, 'Group Administrator')
        retval = 'Became a Group Administrator.'
        return retval

    def removeAdmin(self, userId, auditor):
        roles = list(self.group.get_local_roles_for_userid(userId))
        assert 'GroupAdmin' in roles, '%s was marked for removal '\
          'as a GroupAdmin in %s (%s), but does not have the role.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        roles.remove('GroupAdmin')
        if roles:
            self.group.manage_setLocalRoles(userId, roles)
        else:
            self.group.manage_delLocalRoles([userId])
        auditor.info(LOSE, 'Group Administrator')
        retval = 'No longer a Group Administrator.'
        return retval
    
    def addModerator(self, userId, auditor):
        groupList = self.listInfo.mlist
        moderatorIds = [ m.id for m in self.listInfo.moderators ]
        assert userId not in moderatorIds, '%s was marked for addition '\
          'as a moderator in %s (%s), but is already a moderator.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        moderatorIds.append(userId)
        if groupList.hasProperty('moderator_members'):
            groupList.manage_changeProperties(moderator_members=moderatorIds)
        else:
            groupList.manage_addProperty('moderator_members', moderatorIds, 'lines')
        auditor.info(GAIN, 'Moderator')
        retval = 'Became a Moderator.'
        return retval
        
    def removeModerator(self, userId, auditor):
        groupList = self.listInfo.mlist
        moderatorIds = [ m.id for m in self.listInfo.moderators ]
        assert userId in moderatorIds, '%s was marked for removal '\
          'as a moderator in %s (%s), but is not listed as a moderator.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        moderatorIds.remove(userId)
        if groupList.hasProperty('moderator_members'):
            groupList.manage_changeProperties(moderator_members=moderatorIds)
        else:
            groupList.manage_addProperty('moderator_members', moderatorIds, 'lines')
        auditor.info(LOSE, 'Moderator')
        retval = 'No longer a Moderator.'
        return retval
        
    def moderate(self, userId, auditor):
        groupList = self.listInfo.mlist
        moderatedIds = [ m.id for m in self.listInfo.moderatees ]
        assert userId not in moderatedIds, '%s was marked for '\
          'moderation in %s (%s), but is already moderated.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        moderatedIds.append(userId)
        if groupList.hasProperty('moderated_members'):
            groupList.manage_changeProperties(moderated_members=moderatedIds)
        else:
            groupList.manage_addProperty('moderated_members', moderatedIds, 'lines')
        auditor.info(GAIN, 'Moderated')
        retval = 'Became Moderated.'
        return retval
        
    def unmoderate(self, userId, auditor):
        groupList = self.listInfo.mlist
        moderatedIds = [ m.id for m in self.listInfo.moderatees ]
        assert userId in moderatedIds, '%s was marked to be unmoderated '\
          'in %s (%s), but is not listed as a moderated member.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        moderatedIds.remove(userId)
        if groupList.hasProperty('moderated_members'):
            groupList.manage_changeProperties(moderated_members=moderatedIds)
        else:
            groupList.manage_addProperty('moderated_members', moderatedIds, 'lines')
        auditor.info(LOSE, 'Moderated')
        retval = 'No longer Moderated.'
        return retval
        
    def addPostingMember(self, userId, auditor):
        groupList = self.listInfo.mlist
        postingMemberIds = [ m.id for m in self.listInfo.posting_members ]
        assert userId not in postingMemberIds, '%s was marked to become a '\
          'posting member in %s (%s), but is already a posting member.' %\
           (userId, self.groupInfo.name, groupInfo.id)        
        numPostingMembers = len(postingMemberIds)
        if numPostingMembers >= MAX_POSTING_MEMBERS:
            retval = '***Not become a posting member, as the number of '\
            'posting members is already at the maximum (%d)***' % MAX_POSTING_MEMBERS
            return retval 
        
        postingMemberIds.append(userId)
        if groupList.hasProperty('posting_members'):
            groupList.manage_changeProperties(posting_members=postingMemberIds)
        else:
            groupList.manage_addProperty('posting_members', postingMemberIds, 'lines')
        auditor.info(GAIN, 'Posting Member')
        retval = 'Became a Posting Member'
        return retval

    def removePostingMember(self, userId):
        groupList = self.listInfo.mlist
        postingMemberIds = [ m.id for m in self.listInfo.posting_members ]
        assert userId in postingMemberIds, '%s was marked for removal as '\
          'a posting member in %s (%s), but is not a posting member.' %\
           (userId, self.groupInfo.name, groupInfo.id)
        postingMemberIds.remove(userId)
        if groupList.hasProperty('posting_members'):
            groupList.manage_changeProperties(posting_members=postingMemberIds)
        else:
            groupList.manage_addProperty('posting_members', postingMemberIds, 'lines')
        userInfo = createObject('groupserver.UserFromId', self.group, userId)
        auditor = StatusAuditor(self.group, userInfo)
        auditor.info(LOSE, 'Posting Member')
        retval = 'No longer a Posting Member.'
        return retval
    
    def addPtnCoach(self, ptnCoachToAdd):
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
        userInfo = createObject('groupserver.UserFromId', self.group, ptnCoachToAdd)
        auditor = StatusAuditor(self.group, userInfo)
        auditor.info(GAIN, 'Participation Coach')
        retval = 'Became the Participation Coach.'
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
            
    def removeMember(self, userId):
        userInfo = createObject('groupserver.UserFromId', self.group, userId)
        auditor = StatusAuditor(self.group, userInfo)
        changes = ['Removed from the group.']
        
        # Remove all group roles and positions
        oldPtnCoach = self.groupInfo.ptn_coach
        if oldPtnCoach and (oldPtnCoach.id==userId):
            changes.append(self.removePtnCoach()[1])
        if 'GroupAdmin' in list(self.group.get_local_roles_for_userid(userId)):
            changes.append(self.removeAdmin(userId, auditor))
        if userId in self.listInfo.mlist.getProperty('posting_members', []):
            changes.append(self.removePostingMember(userId))
        if userId in self.listInfo.mlist.getProperty('moderator_members', []):
            changes.append(self.removeModerator(userId, auditor))
        if userId in self.listInfo.mlist.getProperty('moderated_members', []):
            changes.append(self.unmoderate(userId, auditor))

        # Actually remove from group.
        administrator = getSecurityManager().getUser()
        adminInfo = createObject('groupserver.LoggedInUser', self.group)
        ptnCoach = self.groupInfo.ptn_coach
        notifyPtnCoach = ptnCoach and (ptnCoach.id != adminInfo.id)
        userInfo.user.del_groupWithNotification('%s_member' % self.groupInfo.id)
        if notifyPtnCoach:
            n_dict = {
              'groupId'      : self.groupInfo.id,
              'groupName'    : self.groupInfo.name,
              'siteName'     : self.siteInfo.name,
              'canonical'    : getOption(self.group, 'canonicalHost'),
              'supportEmail' : getOption(self.group, 'supportEmail'),
              'memberId'     : userInfo.id,
              'memberName'   : userInfo.name,
              'joining_user' : userInfo.user,
              'joining_group': self.group
            }
            ptnCoach.user.send_notification('leave_group_admin', 
                                self.groupInfo.id, n_dict=n_dict)
        leaveAuditor = LeaveAuditor(self.group, userInfo)
        leaveAuditor.info(REMOVE, userInfo)
        retval = changes
        return retval
        