# coding=utf-8
from zope.component import createObject, adapts
from zope.interface import implements
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import comma_comma_and
from Products.GSContent.interfaces import IGSSiteInfo
from Products.GSGroup.interfaces import IGSGroupInfo
from Products.GSGroupMember.groupmembership import user_division_admin_of_group, \
  user_group_admin_of_group, user_participation_coach_of_group, \
  user_moderator_of_group, user_moderated_member_of_group, \
  user_blocked_member_of_group, user_posting_member_of_group, \
  user_invited_member_of_group, user_member_of_group
from Products.GSGroupMember.interfaces import IGSGroupMembershipStatus

class GSGroupMembershipStatus(object):
    adapts(IGSUserInfo, IGSGroupInfo)
    implements(IGSGroupMembershipStatus)

    def __init__(self, userInfo, groupInfo, siteInfo):
        assert IGSUserInfo.providedBy(userInfo), \
          u'%s is not a GSUserInfo' % userInfo
        assert IGSGroupInfo.providedBy(groupInfo), \
          u'%s is not a GSGroupInfo' % groupInfo
        assert IGSSiteInfo.providedBy(siteInfo), \
          u'%s is not a GSSiteInfo' % siteInfo
        
        self.userInfo = userInfo
        self.groupInfo = groupInfo
        self.siteInfo = siteInfo
        
        self.__status_label = None
        self.__isNormalMember = None
        self.__isConfused = None
        self.__isOddlyConfigured = None
        self.__isSiteAdmin = None
        self.__isGroupAdmin = None
        self.__isPtnCoach = None
        self.__isPostingMember = None
        self.__isModerator = None
        self.__isModerated = None
        self.__isBlocked = None
        self.__isInvited = None
        
        # User Status
        self.__isUnverified = None
        
        # Group Status
        mailingListInfo = \
          createObject('groupserver.MailingListInfo', 
                        self.groupInfo.groupObj)
        self.groupIsModerated = \
          mailingListInfo.is_moderated
        self.postingIsSpecial = \
          self.groupInfo.group_type == 'announcement'
        self.numPostingMembers = \
          len(mailingListInfo.posting_members)

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
        retval = self.__status_label
        assert retval
        return retval

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
              not(self.isSiteAdmin) and \
                not(self.isGroupAdmin) and \
                not(self.isPtnCoach) and \
                not(self.isPostingMember and \
                     (self.groupInfo.group_type == 'announcement')) and \
                not(self.isModerator) and \
                not(self.isModerated) and \
                not(self.isBlocked) and \
                not(self.isInvited) and \
                not(self.isOddlyConfigured)
        retval = self.__isNormalMember
        assert type(retval) == bool
        return retval
    
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
                (self.isPostingMember and \
                  (self.groupInfo.group_type == 'announcement')) or\
                self.isModerator) and \
               (self.isModerated or self.isBlocked or self.isInvited)) or \
              (self.isModerated and (self.isBlocked or self.isInvited)) or \
              (self.isBlocked and self.isInvited)
        retval = self.__isOddlyConfigured
        assert type(retval) == bool
        return retval

    @property
    def isConfused(self):
        if self.__isConfused == None:
            isFullMember = user_member_of_group(self.userInfo, self.groupInfo)
            self.__isConfused = (isFullMember and self.isInvited)
        return self.__isConfused

    @property
    def isSiteAdmin(self):
        if self.__isSiteAdmin == None:
            self.__isSiteAdmin = \
              user_division_admin_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isSiteAdmin
        assert type(retval) == bool
        return retval
        
    @property
    def isGroupAdmin(self):
        if self.__isGroupAdmin == None:
            self.__isGroupAdmin = \
              user_group_admin_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isGroupAdmin
        assert type(retval) == bool
        return retval        

    @property
    def isPtnCoach(self):
        if self.__isPtnCoach == None:
            self.__isPtnCoach = \
              user_participation_coach_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isPtnCoach
        assert type(retval) == bool
        return retval

    @property
    def isPostingMember(self):
        if self.__isPostingMember == None:
            self.__isPostingMember = \
              user_posting_member_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isPostingMember
        assert type(retval) == bool
        return retval

    @property
    def isModerator(self):
        if self.__isModerator == None:
            self.__isModerator = \
              user_moderator_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isModerator
        assert type(retval) == bool
        return retval

    @property
    def isModerated(self):
        if self.__isModerated == None:
            self.__isModerated = \
              user_moderated_member_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isModerated
        assert type(retval) == bool
        return retval

    @property
    def isBlocked(self):
        if self.__isBlocked == None:
            self.__isBlocked = \
              user_blocked_member_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isBlocked
        assert type(retval) == bool
        return retval

    @property
    def isInvited(self):
        if self.__isInvited == None:
            self.__isInvited = \
              user_invited_member_of_group(self.userInfo, \
                self.groupInfo, self.siteInfo)
        retval = self.__isInvited
        assert type(retval) == bool
        return retval

    @property
    def isUnverified(self):
        if self.__isUnverified == None:
            if self.userInfo.user.get_verifiedEmailAddresses():
                self.__isUnverified = False
            else:
                self.__isUnverified = True
        retval = self.__isUnverified
        assert type(retval) == bool
        return retval
    
    
