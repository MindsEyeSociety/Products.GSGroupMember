# coding=utf-8
from zope.interface import implements, providedBy
from zope.component import createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IVocabulary,\
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 
from Products.XWFCore.XWFUtils import getOption
from Products.GSGroupMember.utils import inform_ptn_coach_of_join, invite_id
import time
import AccessControl

from Products.CustomUserFolder.interfaces import IGSUserInfo, ICustomUser
from Products.XWFCore.XWFUtils import sort_by_name
from Products.GSGroup.interfaces import IGSGroupInfo, IGSMailingListInfo
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSGroupMember GroupMembership') #@UndefinedVariable

GROUP_FOLDER_TYPES = ('Folder', 'Folder (Ordered)')

class JoinableGroupsForSite(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, user):
        self.context = user
        self.userInfo = createObject('groupserver.UserFromId', 
                                     user, user.getId())
        self.__groupsInfo = createObject('groupserver.GroupsInfo', user)
        self.siteInfo = createObject('groupserver.SiteInfo', user)
        
        self.__groups = None
       
    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(g.get_id(), g.get_id(), 
                             '%s: for %s' % (g.get_name(),
                                             g.get_property('real_life_group', '')))
                  for g in self.groups]
        for term in retval:
            assert term
            assert ITitledTokenizedTerm in providedBy(term)
            assert term.token == term.value
        return iter(retval)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.groups)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in [g.get_id() for g in self.groups]
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
        for g in self.groups:
            if g.get_id() == token:
                retval = SimpleTerm(g.get_id(), g.get_id(), g.get_name())
                assert retval
                assert ITitledTokenizedTerm in providedBy(retval)
                assert retval.token == retval.value
                return retval
        raise LookupError, token

    @property
    def groups(self):
        assert self.context
        assert self.__groupsInfo
        
        if self.__groups == None:
            gs = self.__groupsInfo.get_joinable_groups_for_user(self.context)
            self.__groups = [createObject('groupserver.GroupInfo', g)
                             for g in gs]
        assert type(self.__groups) == list
        return self.__groups
        
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
        JoinableGroupsForSite.__init__(self, user)
        self.__groups = None
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

        self.viewingUserInfo = createObject('groupserver.LoggedInUser', 
          context)
        
    @property
    def groups(self):
        if self.__groups == None:
            self.__groups = [createObject('groupserver.GroupInfo', g)
                             for g in self.get_invitation_groups()]
            self.__groups.sort(sort_by_name)
        assert type(self.__groups) == list
        return self.__groups

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
          u'(%s) in %.2fms' %\
          (self.userInfo.name, self.userInfo.id, 
           self.viewingUserInfo.name, self.viewingUserInfo.id, 
           self.siteInfo.name, self.siteInfo.id, (bottom-top)*1000.0)
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
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.__members = None
       
    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(u.id, u.id, u.name)
                  for u in self.members]
        for term in retval:
            assert term
            assert ITitledTokenizedTerm in providedBy(term)
            assert term.token == term.value
        return iter(retval)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.members)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in [u.id for u in self.members]
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
        for u in self.members:
            if u.id == token:
                retval = SimpleTerm(u.id, u.id, u.name)
                assert retval
                assert ITitledTokenizedTerm in providedBy(retval)
                assert retval.token == retval.value
                return retval
        raise LookupError, token

    @property
    def members(self):
        assert self.context
        if self.__members == None:
            userIds = get_invited_members(self.context, 
              self.siteInfo.id, self.groupInfo.id)
            self.__members = [ createObject('groupserver.UserFromId', 
                               self.context, uId) for uId in userIds ]
        assert type(self.__members) == list
        #assert reduce(lambda a, b: a and b, 
        #    [IGSUserInfo.providedBy(u) for u in self.__members], True)
        return self.__members

class GroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        self.__members = None
       
    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(u.id, u.id, u.name)
                  for u in self.members]
        for term in retval:
            assert term
            assert ITitledTokenizedTerm in providedBy(term)
            assert term.token == term.value
        return iter(retval)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.members)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in [u.id for u in self.members]
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
        for u in self.members:
            if u.id == token:
                retval = SimpleTerm(u.id, u.id, u.name)
                assert retval
                assert ITitledTokenizedTerm in providedBy(retval)
                assert retval.token == retval.value
                return retval
        raise LookupError, token

    @property
    def members(self):
        assert self.context
        
        if self.__members == None:
            # Get all members of the group
            users = get_group_users(self.context, self.groupInfo.id)
            self.__members = [ createObject('groupserver.UserFromId', 
                                  u, u.getId()) for u in users ]
        assert type(self.__members) == list
        #assert reduce(lambda a, b: a and b, 
        #    [IGSUserInfo.providedBy(u) for u in self.__members], True)
        return self.__members

class SiteMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        
        self.__members = None
       
    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(u.id, u.id,u.name)
                  for u in self.members]
        for term in retval:
            assert term
            assert ITitledTokenizedTerm in providedBy(term)
            assert term.token == term.value
        return iter(retval)

    def __len__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        return len(self.members)

    def __contains__(self, value):
        """See zope.schema.interfaces.IBaseVocabulary"""
        retval = value in [u.id for u in self.members]
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
        for u in self.members:
            if u.id == token:
                retval = SimpleTerm(u.id, u.id, u.name)
                assert retval
                assert ITitledTokenizedTerm in providedBy(retval)
                assert retval.token == retval.value
                return retval
        raise LookupError, token

    @property
    def members(self):
        assert self.context
        
        if self.__members == None:
            # Get all members of the site, who are not members of the group
            users = get_group_users(self.context, self.siteInfo.id)
            self.__members = [createObject('groupserver.UserFromId',  
                                            self.context, u.getId()) 
                             for u in users]
        assert type(self.__members) == list
        return self.__members

class SiteMembersNonGroupMembers(SiteMembers):
    def __init__(self, context):
        SiteMembers.__init__(self, context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        
        self.__members = None

    @property
    def members(self):
        assert self.context
        
        if self.__members == None:
            users = get_group_users(self.context, self.siteInfo.id,
                                    self.groupInfo.id)
            self.__members = [createObject('groupserver.UserFromId',  
                                            self.context, u.getId()) 
                             for u in users]
        assert type(self.__members) == list
        return self.__members

class InviteSiteMembersNonGroupMembers(SiteMembersNonGroupMembers):
    def __init__(self, context):
        SiteMembersNonGroupMembers.__init__(self, context)
        
        self.__members = None
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

    @property
    def members(self):
        assert self.context
        c = self.groupMemberQuery.get_count_current_invitations_in_group
        n = getOption(self.siteInfo.siteObj, 'max_invites_to_group', 5)
        sid = self.siteInfo.id
        gid = self.groupInfo.id
        if self.__members == None:
            # Get all members of the site, who are not members of the group
            users = get_group_users(self.context, sid, gid)
            self.__members = [createObject('groupserver.UserFromId',  
                                            self.context, u.getId()) 
                             for u in users
                             if (c(sid, gid, u.getId())<=n)]
            self.__members.sort(sort_by_name)
        assert type(self.__members) == list
        return self.__members

def get_group_users(context, groupId, excludeGroup = ''):
    '''Get the Members of a User Group
    
    Get the members of the user-group, identified by "groupId" who are
    not members of "excludeGroup"
    '''
    # --mpj17=-- This is slightly wrong. I should get
    #   * All users who have the GroupMember role
    #     group.users_with_local_role('GroupMember')
    #   * All users of all groups that have the GroupMember role
    #     group.groups_with_local_role('GroupMember')
    assert context # What *is* the context?
    assert groupId
    assert type(groupId) == str
    assert type(excludeGroup) == str
    
    memberGroupId  = member_id(groupId)

    site_root = context.site_root()
    assert site_root, 'No site_root'
    assert hasattr(site_root, 'acl_users'), 'No acl_users at site_root'
    acl_users = site_root.acl_users
    memberGroup = acl_users.getGroupById(memberGroupId, [])
    users = [acl_users.getUser(uid) for uid in memberGroup.getUsers()]

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
    da = context.zsqlalchemy 
    assert da, 'No data-adaptor found'
    groupMemberQuery = GroupMemberQuery(da)
    return groupMemberQuery.get_invited_members(siteId, groupId)

def get_unverified_group_users(context, groupId, excludeGroup = ''):
    # AM: To be removed when the new Manage Members code is deployed
    #  and the old admin pages removed.   
    da = context.zsqlalchemy 
    assert da, 'No data-adaptor found'
    groupMemberQuery = GroupMemberQuery(da)

    unverifiedUsers = []
    group_users = get_group_users(context, groupId, excludeGroup)
    for u in group_users:
        if not u.get_verifiedEmailAddresses():
            unverifiedUsers.append(u)
    retval = unverifiedUsers
    assert type(retval)==list
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

def get_groups_on_site(site):
    assert hasattr(site, 'groups'), u'No groups on the site %s' % site.getId()
    groups = getattr(site, 'groups')
    retval = [g for g in \
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
        m = u'(%s) has the GroupMember role for (%s) but is not in  %s'%\
          (user.getId(), group.getId(), memberGroup)
        log.error(m)
    elif not(retval) and (memberGroup in userGroups):
        m = u'(%s) is in %s, but does not have the GroupMember role in (%s)'%\
          (user.getId(), memberGroup, group.getId())
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
    assert IGSUserInfo.providedBy(userInfo), '%s is not a IGSUserInfo' %\
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
    retval = userInfo.id in [ m.id for m in invited_group_members ]
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
      (userInfo.id in [ m.id for m in mlistInfo.moderators ])
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
      (userInfo.id in [ m.id for m in mlistInfo.moderatees ])
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
      (userInfo.id in [ m.id for m in mlistInfo.blocked_members ])
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
      (userInfo.id in [ m.id for m in mlistInfo.posting_members ])
    assert type(retval) == bool
    return retval

def join_group(user, groupInfo):
    '''Join the user to a group
    
    DESCRIPTION
      Joins the user to a group, and the site the group is in 
      (if necessary).
      
    ARGUMENTS
      "user":       The CustomUser that is joined to the group.
      "groupInfo":  The group that the user is joined to.
      
    RETURNS
      None.
      
    SIDE EFFECTS
      The user is a member of the group, and a member of the site that the
      group belongs to.
    '''
    assert ICustomUser.providedBy(user), '%s is not a user' % user
    userInfo = IGSUserInfo(user)
    assert IGSGroupInfo.providedBy(groupInfo), '%s is not a GroupInfo' %\
      groupInfo
    assert not(user_member_of_group(user, groupInfo.groupObj)), \
      'User %s (%s) already in %s (%s)' % \
      (userInfo.name, userInfo.id, groupInfo.name, groupInfo.name)
    
    siteInfo = groupInfo.siteInfo

    m = u'join_group: adding the user %s (%s) to the group %s (%s) '\
        u'on %s (%s)' % \
        (userInfo.name,  userInfo.id,
         groupInfo.name, groupInfo.id,
         siteInfo.name,  siteInfo.id)
    log.info(m)
    user.add_groupWithNotification(member_id(groupInfo.id))

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

def invite_to_groups(userInfo, invitingUserInfo, groups):
    '''Invite the user to join a group
    
    DESCRIPTION
      Invites an existing user to join a group.
      
    ARGUMENTS
      "user":       The CustomUser that is invited to join the group.
      "invitingUserInfo": The user that isi inviting the other to join the 
                          group.
      "groups":  The group (or groups) that the user is joined to.
      
    RETURNS
      None.
      
    SIDE EFFECTS
      An invitation is added to the database, and a notification is
      sent out to the user.
    '''
    assert IGSUserInfo.providedBy(userInfo), '%s is not a IGSUserInfo' %\
      userInfo
    assert IGSUserInfo.providedBy(invitingUserInfo),\
      '%s is not a IGSUserInfo' % userInfo

    # --=mpj17=-- Haskell an his polymorphism can get knotted
    if type(groups) == list:
        groupInfos = groups
    else:
        groupInfos = [groups]
        
    assert groupInfos != []
    
    siteInfo = groupInfos[0].siteInfo

    #--=mpj17=-- Arse to Zope. Really, arse to Zope and its randomly failing
    #            acquisition.
    da = siteInfo.siteObj.aq_parent.aq_parent.zsqlalchemy
    assert da, 'No data-adaptor found'
    groupMemberQuery = GroupMemberQuery(da)

    groupNames = []    
    for groupInfo in groupInfos:
        assert IGSGroupInfo.providedBy(groupInfo)
        assert not(user_member_of_group(userInfo, groupInfo)), \
          'User %s (%s) already in %s (%s)' % \
        (userInfo.name, userInfo.id, groupInfo.name, groupInfo.name)
    
        inviteId = invite_id(siteInfo.id, groupInfo.id, 
                              userInfo.id, invitingUserInfo.id)

        m = u'invite_to_group: %s (%s) inviting %s (%s) to join %s (%s) on '\
          u'%s (%s) with id %s'%\
          (invitingUserInfo.name, invitingUserInfo.id,
            userInfo.name, userInfo.id,
            groupInfo.name, groupInfo.id,
            siteInfo.name, siteInfo.id,
            inviteId)
        log.info(m)
        groupMemberQuery.add_invitation(inviteId, siteInfo.id, groupInfo.id, 
            userInfo.id, invitingUserInfo.id)

        groupNames.append(groupInfo.name)

        if len(groupNames) > 1:
            c = u', '.join(groupNames[:-1])
            g = u' and '.join((c, groupNames[-1]))
        else:
            g = groupNames[0]
    
    responseURL = '%s/r/group_invitation/%s' % (siteInfo.url, inviteId)
    n_dict={'userFn': userInfo.name,
            'invitingUserFn': invitingUserInfo.name,
            'siteName': siteInfo.name,
            'siteURL': siteInfo.url,
            'groupName': g,
            'responseURL': responseURL}
    userInfo.user.send_notification('invite_join_group', 'default', 
        n_dict=n_dict)

