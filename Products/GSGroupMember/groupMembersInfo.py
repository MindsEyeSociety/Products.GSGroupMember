# coding=utf-8
# TODO: Move to gs.group.member.base
from zope.component import createObject
from zope.interface import implements
from Products.XWFCore.XWFUtils import sort_by_name
from gs.profile.email.base.emailuser import EmailUser
from groupmembership import GroupMembers, InvitedGroupMembers
from interfaces import IGSGroupMembersInfo

import logging
log = logging.getLogger('GSGroupMembersInfo')

class GSGroupMembersInfo(object):
    implements(IGSGroupMembersInfo)
    
    def __init__(self, group):
        self.context = group
        self.group = group
        self.mlistInfo = createObject('groupserver.MailingListInfo', group)
        self.groupInfo = self.mlistInfo.groupInfo
        self.siteInfo = createObject('groupserver.SiteInfo', group)
        
        self.__members = self.__memberIds = None
        self.__fullMembers = self.__invitedMembers = None
        
        self.__ptnCoach = None
        self.__groupAdmins = self.__siteAdmins = None
        self.__moderators = self.__moderatees = None
        self.__blockedMembers = self.__postingMembers = None
        self.__unverifiedMembers = self.__managers = None

    # TODO: Add a "normalMembers" property (full members - ptnCoach - admin)

    @property
    def fullMembers(self):
        if self.__fullMembers == None:
            members = GroupMembers(self.context).members
            members.sort(sort_by_name)
            self.__fullMembers = members
        return self.__fullMembers
    
    @property
    def fullMemberCount(self):
        return len(self.fullMembers)
    
    @property
    def invitedMembers(self):
        if self.__invitedMembers == None:
            members = \
              InvitedGroupMembers(self.context, self.siteInfo).members 
            members.sort(sort_by_name)
            self.__invitedMembers = members
        return self.__invitedMembers
    
    @property
    def invitedMemberCount(self):
        return len(self.invitedMembers)
    
    @property
    def members(self):
        if self.__members == None:
            allMembers = self.fullMembers + self.invitedMembers
            fullMemberIds = set([m.id for m in self.fullMembers])
            invitedMemberIds = set([m.id for m in self.invitedMembers])
            distinctMemberIds = fullMemberIds.union(invitedMemberIds)
            members = []
            for uId in distinctMemberIds:
                member = [m for m in allMembers if m.id==uId][0]
                members.append(member)
            members.sort(sort_by_name)
            self.__members = members
        return self.__members

    @property
    def memberIds(self):
        if self.__memberIds == None:
            self.__memberIds = [m.id for m in self.members]
        return self.__memberIds

    @property
    def ptnCoach(self):
        if self.__ptnCoach == None:
            ptnCoachId = self.groupInfo.get_property('ptn_coach_id', '')
            if ptnCoachId and (ptnCoachId in self.memberIds):
                self.__ptnCoach = createObject('groupserver.UserFromId', 
                                      self.context, ptnCoachId)
        return self.__ptnCoach
      
    @property
    def groupAdmins(self):
        if self.__groupAdmins == None:
            admins = self.group.users_with_local_role('GroupAdmin')
            self.__groupAdmins = \
              [ createObject('groupserver.UserFromId', self.context, aId) 
                for aId in admins if aId in self.memberIds ]
        return self.__groupAdmins
      
    @property
    def siteAdmins(self):
        if self.__siteAdmins == None:
            admins = self.siteInfo.site_admins
            self.__siteAdmins = \
              [ a for a in admins if a.id in self.memberIds ]
        return self.__siteAdmins
      
    @property
    def moderators(self):
        if self.__moderators == None:
            self.__moderators = []
            if self.mlistInfo.is_moderated:
                moderators = []
                moderatorIds = self.mlistInfo.get_property('moderator_members') or []
                for uId in moderatorIds:
                    if uId not in self.memberIds:
                        m = u'The user ID %s is listed as a moderator for '\
                          u'the group %s (%s) on the site %s (%s), but is '\
                          u'not a member of the group.' %\
                          (uId, self.groupInfo.name, self.groupInfo.id,
                           self.siteInfo.name, self.siteInfo.id)
                        m = m.encode('ascii', 'ignore')
                        log.warn(m)
                    else:
                        moderators.append(createObject('groupserver.UserFromId', \
                                                       self.context, uId))
                moderators.sort(sort_by_name)
                self.__moderators = moderators
        return self.__moderators
      
    @property
    def moderatees(self):
        if self.__moderatees == None:
            self.__moderatees = []
            if self.mlistInfo.is_moderated:
                moderatees = []
                moderatedIds = self.mlistInfo.get_property('moderated_members') or []
                if moderatedIds:
                    for uId in moderatedIds:
                        if uId not in self.memberIds:
                            m = u'The user ID %s is listed as a moderated member '\
                              u'in the group %s (%s) on the site %s (%s), but is '\
                              u'not a member of the group.' %\
                              (uId, self.groupInfo.name, self.groupInfo.id,
                               self.siteInfo.name, self.siteInfo.id)
                            m = m.encode('ascii', 'ignore')
                            log.warn(m)
                        else:
                            moderatees.append(createObject('groupserver.UserFromId', \
                                                           self.context, uId))
                elif not(self.mlistInfo.is_moderate_new):
                    for u in self.fullMembers:
                        isPtnCoach = self.ptnCoach and (self.ptnCoach.id == u.id) or False
                        isGrpAdmin = u.id in [ a.id for a in self.groupAdmins ]
                        isSiteAdmin = u.id in [ a.id for a in self.siteAdmins ]
                        isModerator = u.id in [ m.id for m in self.moderators ]
                        isBlocked = u.id in [ m.id for m in self.blockedMembers ]
                        if (not(isSiteAdmin) and not(isGrpAdmin) and \
                            not(isPtnCoach) and not(isModerator) and not(isBlocked)):
                            moderatees.append(u)
                moderatees.sort(sort_by_name)
                self.__moderatees = moderatees
        return self.__moderatees
      
    @property
    def blockedMembers(self):
        if self.__blockedMembers == None:
            self.__blockedMembers = []
            blockedIds = self.mlistInfo.get_property('blocked_members') or []
            self.__blockedMembers = [ createObject('groupserver.UserFromId', 
              self.context, uid) for uid in blockedIds ]
        return self.__blockedMembers

    @property
    def postingMembers(self):
        if self.__postingMembers == None:
            self.__postingMembers = self.fullMembers
            postingIds = self.mlistInfo.get_property('posting_members') or []
            if postingIds:
                posters = []
                for uId in postingIds:
                    if uId not in self.memberIds:
                        m = u'The user ID %s is listed as a posting member '\
                          u'in the group %s (%s) on the site %s (%s), but '\
                          u'is not a member of the group.' %\
                          (uId, self.groupInfo.name, self.groupInfo.id,
                           self.siteInfo.name, self.siteInfo.id)
                        m = m.encode('ascii', 'ignore')
                        log.warn(m)
                    else:
                        posters.append(createObject('groupserver.UserFromId', \
                                                    self.context, uId))
                posters.sort(sort_by_name)
                self.__postingMembers = posters
        return self.__postingMembers
    
    @property
    def unverifiedMembers(self):
        if self.__unverifiedMembers == None:
            emailUsers = [ EmailUser(self.context, m) 
                           for m in self.members ]
            members = [ e.userInfo for e in emailUsers 
              if not(e.get_verified_addresses())]
            members.sort(sort_by_name)
            self.__unverifiedMembers = members
        return self.__unverifiedMembers
    
    @property
    def managers(self):
        if self.__managers == None:
            admins = self.groupAdmins + self.siteAdmins
            groupAdminIds = set([a.id for a in self.groupAdmins])
            siteAdminIds = set([a.id for a in self.siteAdmins])
            distinctAdminIds = groupAdminIds.union(siteAdminIds)
            managers = []
            for uId in distinctAdminIds:
                admin = [a for a in admins if a.id==uId][0]
                managers.append(admin)
            managers.sort(sort_by_name)
            self.__managers = managers
        return self.__managers
    
    
