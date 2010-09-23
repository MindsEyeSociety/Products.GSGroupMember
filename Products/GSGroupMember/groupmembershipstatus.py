# coding=utf-8
from zope.component import createObject, adapts
from zope.interface import implements
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import comma_comma_and
from Products.GSGroupMember.interfaces import IGSGroupMembershipStatus, \
  IGSGroupMembersInfo

class GSGroupMembershipStatus(object):
    adapts(IGSUserInfo, IGSGroupMembersInfo)
    implements(IGSGroupMembershipStatus)

    def __init__(self, userInfo, membersInfo):
        assert IGSUserInfo.providedBy(userInfo), \
          u'%s is not a GSUserInfo' % userInfo
        assert IGSGroupMembersInfo.providedBy(membersInfo), \
          u'%s is not a GSGroupMembersInfo' % membersInfo
        
        self.userInfo = userInfo
        self.membersInfo = membersInfo
        self.groupInfo = membersInfo.groupInfo
        self.siteInfo = membersInfo.siteInfo
        self.groupIsModerated = membersInfo.mlistInfo.is_moderated
        self.postingIsSpecial = (self.groupInfo.group_type == 'announcement')
        self.numPostingMembers = len(membersInfo.postingMembers)
        
        self.__status_label = self.__isNormalMember = None
        self.__isSiteAdmin = self.__isGroupAdmin = None
        self.__isPtnCoach = self.__isPostingMember = None
        self.__isModerator = self.__isModerated = None
        self.__isBlocked = self.__isInvited =None
        self.__isMember = self.__isFullMember = None
        self.__isConfused = self.__isOddlyConfigured = None
        self.__isUnverified = None
        
    def __bool__(self):
        return bool(self.isMember)

    def __nonzero__(self):
        return self.__bool__()

    @property
    def status_label(self):
        if self.__status_label == None:
            label = ''            
            statuses = []
            if self.isSiteAdmin:
                statuses.append('Site Administrator')
            if self.isGroupAdmin:
                statuses.append('Group Administrator')
            if self.isPtnCoach:
                statuses.append('Participation Coach')
            if self.postingIsSpecial and self.isPostingMember:
                statuses.append('Posting Member')
            if self.isModerator:
                statuses.append('Moderator')
            if self.isModerated:
                statuses.append('Moderated Member')
            if self.isBlocked:
                statuses.append('Blocked Member')
            if self.isConfused:
                statuses.append('Invited Member (despite already being in the group)')
            elif self.isInvited:
                statuses.append('Invited Member')
            label = comma_comma_and(statuses)

            if not label:
                assert self.isNormalMember
                label = 'Normal Member'
            if self.isOddlyConfigured:
                label = 'Oddly Configured Member: %s' % label
            if self.isUnverified:
                label = '%s with no verified email addresses' % label
            if self.isInvited:
                resendLink = 'resend_invitation.html?form.userId=%s' % \
                  self.userInfo.id
                label = '%s (<a href="%s">Resend Invitation</a>)' %\
                  (label, resendLink) 
            self.__status_label = label
        return self.__status_label

    @property
    def isNormalMember(self):
        if self.__isNormalMember == None:
            # AM: A member is normal if they fulfil ALL of the
            #  following criteria:
            #  * do not hold an administration/management position,
            #  * are not subject to any posting restrictions, and
            #  * are a full member of the group (i.e. must have
            #    accepted an invitation, not just have received one).
            self.__isNormalMember = \
              self.isFullMember and \
              not(self.isSiteAdmin) and \
                not(self.isGroupAdmin) and \
                not(self.isPtnCoach) and \
                not(self.isPostingMember and self.postingIsSpecial) and \
                not(self.isModerator) and \
                not(self.isModerated) and \
                not(self.isBlocked) and \
                not(self.isInvited) and \
                not(self.isOddlyConfigured)
        return self.__isNormalMember
    
    @property
    def isOddlyConfigured(self):
        if self.__isOddlyConfigured == None:
            # AM: A member is oddly configured if they hold an
            #  administration/management position AND: 
            #  * are subjected to posting restrictions, or 
            #  * are not a full member of the group, i.e. 
            #    have only been invited, or have no verified addresses
            # A member is also oddly configured if they are any
            # combination of posting restrictions with only being invited.
            self.__isOddlyConfigured = \
              (self.isConfused or
               (self.isSiteAdmin or 
                self.isGroupAdmin or \
                self.isPtnCoach or \
                (self.isPostingMember and self.postingIsSpecial) or \
                self.isModerator) \
               and \
               (self.isModerated or self.isBlocked or self.isInvited)) \
              or (self.isModerated and (self.isBlocked or self.isInvited)) \
              or (self.isBlocked and self.isInvited)
        return self.__isOddlyConfigured

    @property
    def isSiteAdmin(self):
        if self.__isSiteAdmin == None:
            self.__isSiteAdmin = 'DivisionAdmin' in \
              self.userInfo.user.getRolesInContext(self.groupInfo.groupObj)
        return self.__isSiteAdmin
        
    @property
    def isGroupAdmin(self):
        if self.__isGroupAdmin == None:
            self.__isGroupAdmin = 'GroupAdmin' in \
              self.userInfo.user.getRolesInContext(self.groupInfo.groupObj)
        return self.__isGroupAdmin

    @property
    def isPtnCoach(self):
        if self.__isPtnCoach == None:
            self.__isPtnCoach = self.membersInfo.ptnCoach and \
              (self.membersInfo.ptnCoach.id == self.userInfo.id) or False
        return self.__isPtnCoach

    @property
    def isPostingMember(self):
        if self.__isPostingMember == None:
            self.__isPostingMember = self.userInfo.id in \
              [m.id for m in self.membersInfo.postingMembers]
        return self.__isPostingMember

    @property
    def isModerator(self):
        if self.__isModerator == None:
            self.__isModerator = self.userInfo.id in \
              [m.id for m in self.membersInfo.moderators]
        return self.__isModerator

    @property
    def isModerated(self):
        if self.__isModerated == None:
            self.__isModerated = self.userInfo.id in \
              [m.id for m in self.membersInfo.moderatees]
        return self.__isModerated

    @property
    def isBlocked(self):
        if self.__isBlocked == None:
            self.__isBlocked = self.userInfo.id in \
              [m.id for m in self.membersInfo.blockedMembers]
        return self.__isBlocked
    
    @property
    def isUnverified(self):
        if self.__isUnverified == None:
            self.__isUnverified = self.userInfo.id in \
              [m.id for m in self.membersInfo.unverifiedMembers]
        return self.__isUnverified

    @property
    def isInvited(self):
        if self.__isInvited == None:
            self.__isInvited = self.userInfo.id in \
              [m.id for m in self.membersInfo.invitedMembers]
        return self.__isInvited
    
    @property
    def isFullMember(self):
        if self.__isFullMember == None:
            self.__isFullMember = self.userInfo.id in \
              [m.id for m in self.membersInfo.fullMembers]
        return self.__isFullMember
    
    @property
    def isMember(self):
        if self.__isMember == None:
            self.__isMember = (self.isFullMember or self.isInvited)
        return self.__isMember
    
    @property
    def isConfused(self):
        if self.__isConfused == None:
            self.__isConfused = (self.isFullMember and self.isInvited)
        return self.__isConfused
    
    