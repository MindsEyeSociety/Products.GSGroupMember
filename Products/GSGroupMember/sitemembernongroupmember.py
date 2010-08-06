# coding=utf-8
from zope.interface import implements, providedBy
from zope.component import createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IVocabulary, \
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 

from sitemember import SiteMembers

import logging
log = logging.getLogger('SiteMemberNonGroupMembers') #@UndefinedVariable

class SiteMembersNonGroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.__siteInfo = createObject('groupserver.SiteInfo', context)
        self.__groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.__groupInfo = createObject('groupserver.GroupInfo', context)
        
        self.__acl_users = self.__nonMembers = self.__admin = None
        
        self.siteMembers = SiteMembers(context)

    def __iter__(self):
        """See zope.schema.interfaces.IIterableVocabulary"""
        retval = [SimpleTerm(m.id, m.id, m.name)
                  for m in self.nonMembers]
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
        retval = value in [m.id for m in self.nonMembers]
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
        for m in self.nonMembers:
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

    @property
    def nonMembers(self):
        m = u'Getting the list of members of %s (%s) who are not members '\
          u'of %s (%s)' % \
          (self.__siteInfo.name, self.__siteInfo.id,
           self.__groupInfo.name, self.__groupInfo.id)
        log.info(m)
        
        groupMemberGroupId = '%s_member' % self.__groupInfo.id
        retval = [u for u in self.siteMembers.members
                  if groupMemberGroupId not in 
                    self.acl_users.getUser(u.id).getGroups()]
        return retval

