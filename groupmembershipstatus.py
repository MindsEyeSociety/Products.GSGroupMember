# coding=utf-8
from zope.app.apidoc import interface
from zope.component import createObject, adapts
from zope.interface import implements

from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSGroup.interfaces import IGSGroupInfo, IGSMailingListInfo
from groupmembership import user_division_admin_of_group,\
  user_group_admin_of_group, user_participation_coach_of_group,\
  user_moderator_of_group, user_moderated_member_of_group,\
  user_blocked_member_of_group, user_posting_member_of_group
from Products.XWFCore.XWFUtils import comma_comma_and

import logging
log = logging.getLogger("GSGroupMember.groupmembershipstatus")

class GSGroupMembershipStatus(object):

    adapts(IGSUserInfo, IGSGroupInfo)

    def __init__(self, userInfo, groupInfo):
        assert IGSUserInfo.providedBy(userInfo),\
          u'%s is not a GSUserInfo' % userInfo
        assert IGSGroupInfo.providedBy(groupInfo),\
          u'%s is not a GSGroupInfo' % groupInfo
        
        self.userInfo = userInfo
        self.groupInfo = groupInfo
        self.__status = None
               
    @property
    def status(self):
        retval = ''
        self.__status = retval
        return retval

    @property
    def is_site_admin(self):
        retval = user_division_admin_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval
        
    @property
    def is_group_admin(self):
        retval = user_group_admin_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval        

    @property
    def is_ptn_coach(self):
        retval = user_participation_coach_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval

    @property
    def is_moderator(self):
        retval = user_moderator_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval

    @property
    def is_moderated(self):
        retval = user_moderated_member_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval

    @property
    def is_blocked(self):
        retval = user_blocked_member_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval

    @property
    def is_posting_member(self):
        retval = user_posting_member_of_group(self.userInfo, \
          self.groupInfo)
        assert type(retval) == bool
        return retval

    @property
    def is_unverified_member(self):
        #retval = user_unverified_member_of_group(self.userInfo, \
        #  self.groupInfo)
        retval = False
        assert type(retval) == bool
        return retval

    @property
    def is_normal_member(self):
        retval = not(self.is_site_admin) and \
          not(self.is_group_admin) and \
          not(self.is_ptn_coach) and\
          not(self.is_moderator) and\
          not(self.is_moderated) and\
          not(self.is_blocked) and\
          not(self.is_unverified_member)
        assert type(retval) == bool
        return retval
    
