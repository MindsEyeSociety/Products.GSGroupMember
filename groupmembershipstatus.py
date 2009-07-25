# coding=utf-8
from zope.app.apidoc import interface
from zope.component import createObject, adapts
from zope.interface import implements

from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSGroup.interfaces import IGSGroupInfo, IGSMailingListInfo
from groupmembership import user_division_admin_of_group,\
  user_group_admin_of_group, user_participation_coach_of_group,\
  user_moderator_of_group, user_moderated_member_of_group,\
  user_blocked_member_of_group, user_posting_member_of_group,\
  user_unverified_member_of_group, user_invited_member_of_group
from Products.XWFCore.XWFUtils import comma_comma_and

import logging
log = logging.getLogger("GSGroupMember.groupmembershipstatus")

class GSGroupMembershipStatus(object):

    adapts(IGSUserInfo, IGSGroupInfo)

    def __init__(self, userInfo, groupInfo, siteInfo):
        assert IGSUserInfo.providedBy(userInfo),\
          u'%s is not a GSUserInfo' % userInfo
        assert IGSGroupInfo.providedBy(groupInfo),\
          u'%s is not a GSGroupInfo' % groupInfo
        
        self.userInfo = userInfo
        self.groupInfo = groupInfo
        self.siteInfo = siteInfo
        
        self.__status_label = None
        self.__isNormalMember = None
        self.__isOddlyConfigured = None
        self.__isSiteAdmin = None
        self.__isGroupAdmin = None
        self.__isPtnCoach = None
        self.__isPostingMember = None
        self.__isModerator = None
        self.__isModerated = None
        self.__isBlocked = None
        self.__isUnverified = None
        self.__isInvited = None

    @property
    def status_label(self):
        if self.__status_label == None:
            if self.isNormalMember:
                self.__status_label = 'Normal Member'
            elif self.isOddlyConfigured:
                self.__status_label = 'Oddly Configured Member'
            elif self.isInvited:
                self.__status_label = 'Invited Member'
            else:
                postingIsSpecial = (self.groupInfo.group_type == 'announcement')
                statuses = []
                if self.isSiteAdmin:
                    statuses.append('Site Administrator')
                if self.isGroupAdmin:
                    statuses.append('Group Administrator')
                if self.isPtnCoach:
                    statuses.append('Participation Coach')
                if self.isPostingMember and postingIsSpecial:
                    statuses.append('Posting Member')
                if self.isModerator:
                    statuses.append('Moderator')
                if self.isModerated:
                    statuses.append('Moderated Member')
                if self.isBlocked:
                    statuses.append('Blocked Member')
                if self.isUnverified:
                    statuses.append('Invited Member')
                self.__status_label = comma_comma_and(statuses)
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
                not(self.isUnverified) and \
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
              ((self.isSiteAdmin or 
                self.isGroupAdmin or \
                self.isPtnCoach or \
                (self.isPostingMember and \
                  (self.groupInfo.group_type == 'announcement')) or\
                self.isModerator) and \
               (self.isModerated or self.isBlocked or \
                self.isUnverified or self.isInvited)) or \
              (self.isModerated and (self.isBlocked or self.isInvited)) or \
              (self.isBlocked and self.isInvited)
        retval = self.__isOddlyConfigured
        assert type(retval) == bool
        return retval

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
    def isUnverified(self):
        if self.__isUnverified == None:
            self.__isUnverified = \
              user_unverified_member_of_group(self.userInfo, \
                self.groupInfo)
        retval = self.__isUnverified
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
