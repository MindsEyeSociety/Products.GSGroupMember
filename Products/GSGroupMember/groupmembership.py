# coding=utf-8
import time
from zope.cachedescriptors.property import Lazy
from zope.component import createObject
from zope.interface import implements, providedBy
from zope.interface.common.mapping import IEnumerableMapping
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IVocabulary, \
    IVocabularyTokenized, ITitledTokenizedTerm
from Products.XWFCore.XWFUtils import getOption
from Products.GSGroupMember.utils import inform_ptn_coach_of_join
from Products.CustomUserFolder.interfaces import IGSUserInfo, ICustomUser
from Products.XWFCore.XWFUtils import sort_by_name
from Products.GSGroup.interfaces import IGSGroupInfo, IGSMailingListInfo
from gs.profile.email.base.emailuser import EmailUser
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSGroupMember GroupMembership')

GROUP_FOLDER_TYPES = ('Folder', 'Folder (Ordered)')


class JoinableGroupsForSite(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, user):
        self.context = self.user = user
        assert self.context

    @Lazy
    def userInfo(self):
        retval = createObject('groupserver.UserFromId', self.user,
                            self.user.getId())
        return retval

    @Lazy
    def siteInfo(self):
        retval = createObject('groupserver.SiteInfo', self.user)
        return retval

    @Lazy
    def groupsInfo(self):
        retval = createObject('groupserver.GroupsInfo', self.user)
        return retval

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        for g in self.groups:
            n = '%s: %s' % (g.name, g.get_property('description', ''))
            retval = SimpleTerm(g.id, g.id, n)
            assert ITitledTokenizedTerm in providedBy(retval)
            assert retval.token == retval.value
            assert retval.token == g.id
            yield retval

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.groups)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in self.groupIds
        assert type(retval) == bool
        return retval

    def getQuery(self):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return None

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return self.getTermByToken(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        if token in self:
            g = createObject('groupserver.GroupInfo', self.context, token)
            n = '%s: %s' % (g.name, g.get_property('description', ''))
            retval = SimpleTerm(g.id, g.id, n)
        else:
            raise LookupError(token)
        assert retval
        assert ITitledTokenizedTerm in providedBy(retval)
        assert retval.token == retval.value
        assert retval.token == token
        return retval

    @Lazy
    def groupIds(self):
        retval = [g.id for g in self.groups]
        return retval

    @Lazy
    def groups(self):
        gs = self.groupsInfo.get_joinable_groups_for_user(self.context)
        retval = [createObject('groupserver.GroupInfo', g) for g in gs]
        assert type(retval) == list
        return retval


class InvitationGroupsForSite(JoinableGroupsForSite):
    '''Get the invitation groups for the current site

    DESCRIPTION
      Invitation groups are those that the user can be invited
      to join by the viewing user.

      Technically, they are groups the user ("context") is not a member
      of, but the viewing user
      ("AccessControl.getSecurityManager().getUser()") has administrator
      rights to and the user (context) has not been invited to too much.
    '''
    def __init__(self, user, context):
        JoinableGroupsForSite.__init__(self, context.user)

    @Lazy
    def viewingUserInfo(self):
        retval = createObject('groupserver.LoggedInUser', self.context)
        return retval

    @Lazy
    def groupMemberQuery(self):
        retval = GroupMemberQuery()
        return retval

    @Lazy
    def groups(self):
        retval = [createObject('groupserver.GroupInfo', g)
                     for g in self.get_invitation_groups()]
        retval.sort(sort_by_name)
        assert type(retval) == list
        return retval

    def get_invitation_groups(self):
        assert self.siteInfo
        top = time.time()

        siteGroups = get_groups_on_site(self.siteInfo.siteObj)
        user = self.userInfo.user
        admin = self.viewingUserInfo.user
        c = self.groupMemberQuery.get_count_current_invitations_in_group
        u = self.userInfo
        n = getOption(user, 'max_invites_to_group', 5)
        retval = [g for g in siteGroups
                  if (not(user_member_of_group(user, g))
                      and user_admin_of_group(admin, g)
                      and (c(self.siteInfo.id, g.getId(), u.id) <= n))]

        bottom = time.time()
        m = u'Generated invitation groups of %s (%s) for %s (%s) on %s '\
          u'(%s) in %.2fms' % \
          (self.userInfo.name, self.userInfo.id,
           self.viewingUserInfo.name, self.viewingUserInfo.id,
           self.siteInfo.name, self.siteInfo.id, (bottom - top) * 1000.0)
        log.info(m)

        assert type(retval) == list
        return retval


class InvitationGroupsForSiteAndCurrentUser(InvitationGroupsForSite):
    def __init__(self, context):
        InvitationGroupsForSite.__init__(self, context, context)

###########
# Members #
###########


class InvitedGroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context, siteInfo):
        self.context = context
        self.siteInfo = siteInfo
        assert self.context

    @Lazy
    def groupInfo(self):
            retval = createObject('groupserver.GroupInfo', self.context)
            return retval

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        for uid in self.memberIds:
            u = createObject('groupserver.UserFromId', self.context, uid)
            retval = SimpleTerm(u.id, u.id, u.name)
            assert retval
            assert ITitledTokenizedTerm in providedBy(retval)
            assert retval.token == retval.value
            yield retval

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.memberIds)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in self.memberIds
        assert type(retval) == bool
        return retval

    def getQuery(self):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return None

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return self.getTermByToken(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        if token in self:
            u = createObject('groupserver.UserFromId', self.context, token)
            retval = SimpleTerm(u.id, u.id, u.name)
        else:
            raise LookupError(token)
        assert retval
        assert ITitledTokenizedTerm in providedBy(retval)
        assert retval.token == retval.value
        return retval

    @Lazy
    def memberIds(self):
        retval = get_invited_members(self.context, self.siteInfo.id,
                                        self.groupInfo.id)
        return retval

    @Lazy
    def members(self):
        ms = [createObject('groupserver.UserFromId', self.context, uId)
                    for uId in self.memberIds]
        retval = [m for m in ms if not m.anonymous]
        assert type(retval) == list
        #assert reduce(lambda a, b: a and b,
        #    [IGSUserInfo.providedBy(u) for u in self.__members], True)
        return retval


class GroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.__members = None
        assert self.context

    @Lazy
    def groupInfo(self):
        retval = createObject('groupserver.GroupInfo', self.context)
        return retval

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        for uid in self.memberIds:
            u = createObject('groupserver.UserFromId', self.context, uid)
            term = SimpleTerm(u.id, u.id, u.name)
            assert term
            assert ITitledTokenizedTerm in providedBy(term)
            assert term.token == term.value
            yield term

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.member_ids)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in self.member_ids
        assert type(retval) == bool
        return retval

    def getQuery(self):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return None

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return self.getTermByToken(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        if token in self.member_ids:
            u = createObject('groupserver.UserFromId', self.context, token)
            retval = SimpleTerm(u.id, u.id, u.name)
        else:
            raise LookupError(token)
        assert retval
        assert ITitledTokenizedTerm in providedBy(retval)
        assert retval.token == retval.value
        return retval

    @Lazy
    def member_ids(self):
        assert self.context
        userIds = get_group_userids(self.context, self.groupInfo.id)
        return userIds

    @property
    def members(self):
        if self.__members is None:
            # Get all members of the group
            member_ids = self.member_ids
            self.__members = [createObject('groupserver.UserFromId',
                                  self.context, mid) for mid in member_ids]
        assert type(self.__members) == list
        #assert reduce(lambda a, b: a and b,
        #    [IGSUserInfo.providedBy(u) for u in self.__members], True)
        return self.__members


class SiteMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        assert self.context

    @Lazy
    def siteInfo(self):
        retval = createObject('groupserver.SiteInfo', self.context)
        return retval

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        for uid in self.memberIds:
            u = createObject('groupserver.UserFromId', self.context, uid)
            retval = SimpleTerm(u.id, u.id, u.name)
            assert retval
            assert ITitledTokenizedTerm in providedBy(retval)
            assert retval.token == retval.value
            yield retval

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.memberIds)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in self.memberIds
        assert type(retval) == bool
        return retval

    def getQuery(self):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return None

    def getTerm(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        return self.getTermByToken(value)

    def getTermByToken(self, token):
        """See zope.schema.interfaces.IVocabularyTokenized"""
        if token in self:
            u = createObject('groupserver.UserFromId', self.context, token)
            retval = SimpleTerm(u.id, u.id, u.name)
        else:
            raise LookupError(token)
        assert retval
        assert ITitledTokenizedTerm in providedBy(retval)
        assert retval.token == retval.value
        return retval

    @Lazy
    def memberIds(self):
        retval = get_group_userids(self.context, self.siteInfo.id)
        return retval

    @Lazy
    def members(self):
        # Get all members of the site, who are not members of the group
        retval = [createObject('groupserver.UserFromId', self.context, uid)
                    for uid in self.memberIds]
        assert type(retval) == list
        return self.retval


class SiteMembersNonGroupMembers(SiteMembers):
    def __init__(self, context):
        SiteMembers.__init__(self, context)

    @Lazy
    def groupInfo(self):
        retval = createObject('groupserver.GroupInfo', self.context)
        return retval

    @Lazy
    def members(self):
        users = get_group_userids(self.context, self.siteInfo.id,
                                self.groupInfo.id)
        retval = [createObject('groupserver.UserFromId', self.context, uid)
                    for uid in users]
        assert type(retval) == list
        return retval


class InviteSiteMembersNonGroupMembers(SiteMembersNonGroupMembers):
    def __init__(self, context):
        SiteMembersNonGroupMembers.__init__(self, context)

    @Lazy
    def groupMemberQuery(self):
        retval = GroupMemberQuery()
        return retval

    @Lazy
    def members(self):
        assert self.context
        c = self.groupMemberQuery.get_count_current_invitations_in_group
        n = getOption(self.siteInfo.siteObj, 'max_invites_to_group', 5)
        sid = self.siteInfo.id
        gid = self.groupInfo.id

        # Get all members of the site, who are not members of the group
        users = get_group_userids(self.context, sid, gid)
        retval = [createObject('groupserver.UserFromId', self.context, uid)
                    for uid in users if (c(sid, gid, uid) <= n)]
        retval.sort(sort_by_name)
        assert type(retval) == list
        return retval


def get_group_userids(context, groupId):
    '''Get the user Ids of members of a user group.
    '''
    assert context
    assert groupId
    assert type(groupId) == str

    memberGroupId = member_id(groupId)

    site_root = context.site_root()
    assert site_root, 'No site_root'
    assert hasattr(site_root, 'acl_users'), 'No acl_users at site_root'
    acl_users = site_root.acl_users
    memberGroup = acl_users.getGroupById(memberGroupId, [])
    retval = list(memberGroup.getUsers())

    assert type(retval) == list, 'retval is a %s, not a list.' % type(retval)
    return retval


def get_group_users(context, groupId, excludeGroup=''):
    '''Get the Members of a User Group

    Get the members of the user-group, identified by "groupId" who are
    not members of "excludeGroup"
    '''
    # --mpj17=-- This is slightly wrong. I should get
    #   * All users who have the GroupMember role
    #     group.users_with_local_role('GroupMember')
    #   * All users of all groups that have the GroupMember role
    #     group.groups_with_local_role('GroupMember')
    assert type(excludeGroup) == str

    site_root = context.site_root()
    assert site_root, 'No site_root'
    assert hasattr(site_root, 'acl_users'), 'No acl_users at site_root'
    acl_users = site_root.acl_users
    users = [acl_users.getUser(uid)
                for uid in get_group_userids(context, groupId)]

    if excludeGroup != '':
        memberExcludeGroup = member_id(excludeGroup)
        retval = []
        for u in users:
            if memberExcludeGroup not in u.getGroups():
                retval.append(u)
    else:
        retval = users
    assert type(retval) == list
    # --=mpj17=-- I should really check that I am actually returning users.
    #assert reduce(lambda a, b: a and b,
    #              [ICustomUser.providedBy(u) for u in retval], True)
    return retval


def get_invited_members(context, siteId, groupId):
    groupMemberQuery = GroupMemberQuery()
    return groupMemberQuery.get_invited_members(siteId, groupId)


def get_unverified_group_users(context, groupId, excludeGroup=''):
    # AM: To be removed when the new Manage Members code is deployed
    #  and the old admin pages removed.
    unverifiedUsers = []
    group_users = get_group_users(context, groupId, excludeGroup)
    for u in group_users:
        eu = EmailUser(context, u)
        if not eu.get_verified_addresses():
            unverifiedUsers.append(u)
    retval = unverifiedUsers
    assert type(retval) == list
    return retval


#############
# Utilities #
#############

def member_id(groupId):
    assert type(groupId) == str
    assert groupId != ''

    retval = '%s_member' % groupId

    assert type(retval) == str
    return retval


def groupInfo_to_group(g):
    if IGSGroupInfo.providedBy(g):
        group = g.groupObj
    else:
        group = g
    return group


def userInfo_to_user(u):
    if IGSUserInfo.providedBy(u):
        user = u.user
    else:
        user = u
    return user


def user_to_userInfo(u):
    if ICustomUser.providedBy(u):
        user = IGSUserInfo(u)
    else:
        user = u
    return user


def get_groups_on_site(site):
    assert hasattr(site, 'groups'), u'No groups on the site %s' % site.getId()
    groups = getattr(site, 'groups')
    retval = [g for g in
              groups.objectValues(GROUP_FOLDER_TYPES)
              if g.getProperty('is_group', False)]
    assert type(retval) == list
    return retval

#####################
# Membership Checks #
#####################


def user_member_of_group(u, g):
    '''Is the user the member of the group

    ARGUMENTS
        "user":  A Custom User.
        "group": A GroupServer group-folder.

    RETURNS
        True if the user is the member of the group. False otherwise.
    '''
    group = groupInfo_to_group(g)
    user = userInfo_to_user(u)

    retval = 'GroupMember' in user.getRolesInContext(group)

    # Thundering great sanity check
    memberGroup = member_id(group.getId())
    userGroups = user.getGroups()
    if retval and (memberGroup not in userGroups):
        m = u'(%s) has the GroupMember role for (%s) but is not in  %s' % \
          (user.getId(), group.getId(), memberGroup)
        log.error(m)
    elif not(retval) and (memberGroup in userGroups):
        m = u'(%s) is in %s, but does not have the GroupMember role in '\
            u'(%s)' % (user.getId(), memberGroup, group.getId())
        log.error(m)

    assert type(retval) == bool
    return retval
    return user


def user_member_of_site(user, site):
    retval = 'DivisionMember' in user.getRolesInContext(site)
    assert type(retval) == bool
    return retval


def user_admin_of_group(u, g):
    group = groupInfo_to_group(g)
    user = userInfo_to_user(u)
    retval = (user_group_admin_of_group(user, group) or
              user_division_admin_of_group(user, group))
    assert type(retval) == bool
    return retval


def user_group_admin_of_group(u, g):
    group = groupInfo_to_group(g)
    user = userInfo_to_user(u)
    retval = ('GroupAdmin' in user.getRolesInContext(group))
    assert type(retval) == bool
    return retval


def user_division_admin_of_group(u, g):
    group = groupInfo_to_group(g)
    user = userInfo_to_user(u)
    retval = ('DivisionAdmin' in user.getRolesInContext(group))
    assert type(retval) == bool
    return retval


def user_participation_coach_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), '%s is not a IGSUserInfo' % \
      userInfo
    assert IGSGroupInfo.providedBy(groupInfo)
    ptnCoachId = groupInfo.get_property('ptn_coach_id', '')
    retval = user_member_of_group(userInfo, groupInfo)\
      and (userInfo.id == ptnCoachId)
    assert type(retval) == bool
    return retval


def user_unverified_member_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not a IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    unverified_group_members = \
      get_unverified_group_users(context, groupInfo.id)
    retval = user_member_of_group(userInfo, groupInfo)\
      and (userInfo.id in [m.getId() for m in unverified_group_members])
    assert type(retval) == bool
    return retval


def user_invited_member_of_group(userInfo, groupInfo, siteInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not a IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    invited_group_members = \
      InvitedGroupMembers(context, siteInfo).members
    retval = userInfo.id in [m.id for m in invited_group_members]
    assert type(retval) == bool
    return retval


def user_moderator_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not an IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    mlistInfo = IGSMailingListInfo(context)
    retval = user_member_of_group(userInfo, groupInfo) and \
      (userInfo.id in [m.id for m in mlistInfo.moderators])
    assert type(retval) == bool
    return retval


def user_moderated_member_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not an IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    mlistInfo = IGSMailingListInfo(context)
    retval = user_member_of_group(userInfo, groupInfo) and \
      (userInfo.id in [m.id for m in mlistInfo.moderatees])
    assert type(retval) == bool
    return retval


def user_blocked_member_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not an IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    mlistInfo = createObject('groupserver.MailingListInfo', context)
    retval = user_member_of_group(userInfo, groupInfo) and \
      (userInfo.id in [m.id for m in mlistInfo.blocked_members])
    assert type(retval) == bool
    return retval


def user_posting_member_of_group(userInfo, groupInfo):
    assert IGSUserInfo.providedBy(userInfo), \
      '%s is not an IGSUserInfo' % userInfo
    assert IGSGroupInfo.providedBy(groupInfo), \
      '%s is not an IGSGroupInfo' % groupInfo
    context = groupInfo.groupObj
    mlistInfo = IGSMailingListInfo(context)
    retval = user_member_of_group(userInfo, groupInfo) and \
      (userInfo.id in [m.id for m in mlistInfo.posting_members])
    assert type(retval) == bool
    return retval


def join_group(u, groupInfo):
    '''Join the user to a group

    DESCRIPTION
      Joins the user to a group, and the site the group is in
      (if necessary).

    ARGUMENTS
      "user":       The user that is joined to the group.
      "groupInfo":  The group that the user is joined to.

    RETURNS
      None.

    SIDE EFFECTS
      The user is a member of the group, and a member of the site that the
      group belongs to.
    '''
    userInfo = user_to_userInfo(u)
    user = userInfo_to_user(u)
    assert IGSGroupInfo.providedBy(groupInfo), '%s is not a GroupInfo' % \
      groupInfo
    assert not(user_member_of_group(user, groupInfo.groupObj)), \
      u'User %s (%s) already in %s (%s)' % \
      (userInfo.name, userInfo.id, groupInfo.name, groupInfo.name)

    siteInfo = groupInfo.siteInfo

    m = u'join_group: adding the user %s (%s) to the group %s (%s) '\
        u'on %s (%s)' % \
        (userInfo.name, userInfo.id,
         groupInfo.name, groupInfo.id,
         siteInfo.name, siteInfo.id)
    log.info(m)
    user.add_groupWithNotification(member_id(groupInfo.id))

    # TODO: Change to all group admins
    #  <https://projects.iopen.net/groupserver/ticket/410>
    ptnCoachId = groupInfo.get_property('ptn_coach_id', '')
    if ptnCoachId:
        ptnCoachInfo = createObject('groupserver.UserFromId',
                                     groupInfo.groupObj, ptnCoachId)
        inform_ptn_coach_of_join(ptnCoachInfo, userInfo, groupInfo)

    if not(user_member_of_site(user, siteInfo.siteObj)):
        m = u'join_group: the user %s (%s) is not a '\
            u' member of the site %s (%s)' % \
              (userInfo.name, userInfo.id, siteInfo.name, siteInfo.id)
        log.info(m)
        user.add_groupWithNotification(member_id(siteInfo.id))

    assert user_member_of_group(user, groupInfo.groupObj)
    assert user_member_of_site(user, siteInfo.siteObj)
