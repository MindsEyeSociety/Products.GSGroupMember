# coding=utf-8
from zope.interface import implements, alsoProvides, providedBy
from zope.component import getUtility, createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import ITokenizedTerm, IVocabulary,\
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 

from Products.CustomUserFolder.interfaces import IGSUserInfo

import logging
log = logging.getLogger('SiteMember')

class SiteMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.__siteInfo = createObject('groupserver.SiteInfo', context)
        self.__groupsInfo = createObject('groupserver.GroupsInfo', context)
        
        self.__acl_users = self.__members = self.__admin = None

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(m.id, m.id, m.name)
                  for m in self.members]
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
        retval = value in [m.id for m in self.members]
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
        for m in self.members:
            if m.id == token:
                retval = SimpleTerm(m.id, m.id, m.name)
                assert retval
                assert ITitledTokenizedTerm in providedBy(retval)
                assert retval.token == retval.value
                return retval
        raise LookupError, token

    @property
    def admin(self):
        if self.__admin == None:
            self.__admin = self.request.AUTHENTICATED_USER
            assert self.__admin
            self.__adminInfo = IGSUserInfo(self.__admin)
            roles = self.__admin.getRolesInContext(self.groupInfo.groupObj)
            assert ('GroupAdmin' in roles) or ('DivisionAdmin' in roles), \
              '%s (%s) is not an administrator of %s (%s) on %s (%s)' % \
                (self.__adminInfo.name, self.__adminInfo.id, 
                 self.groupInfo.name, self.groupInfo.id,
                 self.siteInfo.get_name(), self.siteInfo.get_id())
        return self.__admin

    @property
    def acl_users(self):
        if self.__acl_users == None:
            self.__acl_users = \
              getattr(self.siteInfo.siteObj.site_root(), 'acl_users', None)
        assert self.__acl_users
        return self.__acl_users        
  
    def get_site_member_group_user_ids(self):
        siteMemberGroupId = '%s_member' % self.siteInfo.id
        siteMemberGroup = self.acl_users.getGroupById(siteMemberGroupId)

        assert siteMemberGroup,\
          u'Could not get site-member group for %s (%s)' %\
          (self.siteInfo.name, self.siteInfo.id)
        assert type(siteMemberGroup) == list
        types = [type(u)==str for u in siteMemberGroup]
        assert reduce(lambda a, b: a and b, types, True),\
          u'Not all strings returned'
        return siteMemberGroup
        
    @property
    def members(self):
        assert self.context
        assert self.__siteInfo
        if self.__members == None:
            userId = self.context.getId()
            m = u'Generating membership list for %s (%s) for %s (%s)' %\
              (self.admin.name, self.admin.id,
               self.siteInfo.name, self.siteInfo.id)
            log.info(m)
            siteMemberGroupIds = self.get_site_member_group_user_ids()
            self.__members = [createObject('groupserver.UserFromId', uid)
              for uid in siteMemberGroup]
        assert type(self.__members) == list
        return self.__members

