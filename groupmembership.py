# coding=utf-8
import time
from zope.interface import implements, alsoProvides, providedBy
from zope.component import getUtility, createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import ITokenizedTerm, IVocabulary,\
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 
import AccessControl

from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFCore.XWFUtils import getOption
from queries import GroupMemberQuery

import logging
log = logging.getLogger('GSGroupMember GroupMembership')

GROUP_FOLDER_TYPES = ('Folder', 'Folder (Ordered)')

class JoinableGroupsForSite(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.userInfo = createObject('groupserver.UserFromId', 
                                     context, context.getId())
        self.__userId = context.getId()
        self.__groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        
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
        retval = False
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
            userId = self.context.getId()
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
    def __init__(self, context):
        JoinableGroupsForSite.__init__(self, context)
        self.__groups = None
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.groupMemberQuery = GroupMemberQuery(da)

        viewingUser = AccessControl.getSecurityManager().getUser()
        self.viewingUserInfo = createObject('groupserver.UserFromId', 
          context, viewingUser.getId())
        
    @property
    def groups(self):
        if self.__groups == None:
            self.__groups = [createObject('groupserver.GroupInfo', g)
                             for g in self.get_invitation_groups()]
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
        retval = False
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
        assert type(self.__members) == list
        return self.__members

def get_group_users(context, groupId, excludeGroup = None):
    '''Get the Members of a User Group
    
    Get the members of the user-group, identified by "groupId" who are
    not members of "excludeGroup"
    '''
    assert context # What *is* the context?
    assert groupId
    assert type(groupId) == str
    assert type(excludeGroup) == str
    
    memberGroupId  = '%s_member' % groupId

    site_root = context.site_root()
    assert site_root, 'No site_root'
    assert hasattr(site_root, 'acl_users'), 'No acl_users at site_root'
    acl_users = site_root.acl_users
    memberGroup = acl_users.getGroupById(memberGroupId, [])
    users = [acl_users.getUser(uid) for uid in memberGroup.getUsers()]

    if excludeGroup:
        memberExcludeGroup = '%s_member' % excludeGroup
        retval = []
        for u in users:
            if memberExcludeGroup not in u.getGroups():
                retval.append(u)
    else:
        retval = users
    assert type(retval) == list
    # --=mpj17=-- I should really check that I am actually returning users.
    return retval

def get_groups_on_site(site):
    retval = []
    assert hasattr(site, 'groups'), u'No groups on the site %s' % site.getId()
    groups = getattr(site, 'groups')
    retval = [g for g in \
              groups.objectValues(GROUP_FOLDER_TYPES)
              if g.getProperty('is_group', False)]
    assert type(retval) == list
    return retval

def user_member_of_group(user, group):
    retval = 'GroupMember' in user.getRolesInContext(group)
    assert type(retval) == bool
    return retval
    
def user_admin_of_group(user, group):
    retval = (user_group_admin_of_group(user, group) or 
              user_division_admin_of_group(user, group))
    assert type(retval) == bool
    return retval

def user_group_admin_of_group(user, group):
    retval = ('GroupAdmin' in user.getRolesInContext(group))
    assert type(retval) == bool
    return retval

def user_division_admin_of_group(user, group):
    retval = ('DivisionAdmin' in user.getRolesInContext(group))
    assert type(retval) == bool
    return retval

