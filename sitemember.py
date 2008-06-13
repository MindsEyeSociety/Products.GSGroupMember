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
    def acl_users(self):
        if self.__acl_users == None:
            sr = self.context.site_root()
            assert sr, 'No site root'
            self.__acl_users = sr.acl_users
        assert self.__acl_users, 'No ACL Users'
        return self.__acl_users        
  
    def get_site_member_group_user_ids(self):
        siteMemberGroupId = '%s_member' % self.__siteInfo.id
        siteMemberGroup = self.acl_users.getGroupById(siteMemberGroupId)
        assert siteMemberGroup,\
          u'Could not get site-member group for %s (%s)' %\
          (self.__siteInfo.name, self.__siteInfo.id)
  
        retval = [uid for uid in siteMemberGroup.getUsers() 
                  if self.acl_users.getUser(uid)]
        assert type(retval) == list,\
          'Retval is a %s, not a list' % type(siteMemberGroup)
        types = [type(u)==str for u in retval]
        assert reduce(lambda a, b: a and b, types, True),\
          u'Not all strings returned'
        return retval
        
    @property
    def members(self):
        assert self.context
        assert self.__siteInfo
        if self.__members == None:
            userId = self.context.getId()
            m = u'Generating membership list for %s (%s)' %\
              (self.__siteInfo.name, self.__siteInfo.id)
            log.info(m)
            siteMemberGroupIds = self.get_site_member_group_user_ids()
            self.__members =\
              [createObject('groupserver.UserFromId', self.context, uid)
               for uid in siteMemberGroupIds]
        assert type(self.__members) == list
        return self.__members

