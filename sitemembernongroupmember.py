# coding=utf-8
from zope.interface import implements, alsoProvides, providedBy
from zope.component import getUtility, createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import ITokenizedTerm, IVocabulary,\
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 

from Products.CustomUserFolder.interfaces import IGSUserInfo

from sitemember import SiteMembers

import logging
log = logging.getLogger('SiteMemberNonGroupMembers')

class SiteMembersNonGroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
        self.__siteInfo = createObject('groupserver.SiteInfo', context)
        self.__groupsInfo = createObject('groupserver.GroupsInfo', context)
        self.__groupInfo =  createObject('groupserver.GroupInfo', context)
        
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
        retval = False
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
    def nonMembers(self):
        m = u'Getting the list of members of %s (%s) who are not members '\
          u'of %s (%s) for %s (%s)' %\
          (self.__siteInfo.name, self.__siteInfo.id,
           self.__groupInfo.name, self.__groupInfo.id, 
           self.admin.name, self.admin.id)
        log.info(m)
        
        groupMemberGroupId = '%s_member' % self.__groupInfo.id
        retval = [u for u in self.siteMembers.members
                  if groupMemberGroupId not in 
                    self.acl_users.getUser(u.id).getGroups()]
        return retval

