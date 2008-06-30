# coding=utf-8
import time
from zope.interface import implements, alsoProvides, providedBy
from zope.component import getUtility, createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import ITokenizedTerm, IVocabulary,\
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 
import AccessControl

from Products.CustomUserFolder.userinfo import GSUserInfo

import logging
log = logging.getLogger('GSGroupMember GroupMembership')

GROUP_FOLDER_TYPES = ('Folder', 'Folder (Ordered)')

class JoinableGroupsForSite(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.userInfo = GSUserInfo(context)
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
      rights to.
    '''
    def __init__(self, context):
        JoinableGroupsForSite.__init__(self, context)
        self.__groups = None
                
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
        retval = [g for g in siteGroups 
                  if (not(user_member_of_group(user, g))
                      and user_admin_of_group(admin, g))]

        bottom = time.time()
        m = u'Generated invitation groups of %s (%s) for %s (%s) on %s '\
          u'(%s) in %.2fms' %\
          (self.userInfo.name, self.userInfo.id, 
           self.viewingUserInfo.name, self.viewingUserInfo.id, 
           self.siteInfo.name, self.siteInfo.id, (bottom-top)*1000.0)
        log.info(m)        

        assert type(retval) == list
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

