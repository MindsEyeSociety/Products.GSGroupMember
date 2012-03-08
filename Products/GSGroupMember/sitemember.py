# coding=utf-8
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, providedBy
from zope.component import createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IVocabulary, \
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 

import logging
log = logging.getLogger('SiteMember') #@UndefinedVariable

class SiteMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
    
    @Lazy
    def siteInfo(self):
        retval = createObject('groupserver.SiteInfo', self.context)
        return retval
    
    @Lazy
    def groupsInfo(self):
        retval = createObject('groupserver.GroupsInfo', self.context)
        return retval
    
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
        
    @Lazy
    def acl_users(self):
        sr = self.context.site_root()
        assert sr, 'No site root'
        retval = sr.acl_users
        assert retval, 'No ACL Users'
        return retval
  
    def get_site_member_group_user_ids(self):
        siteMemberGroupId = '%s_member' % self.siteInfo.id
        smg = self.acl_users.getGroupById(siteMemberGroupId)
        assert smg, u'Could not get site-member group for %s (%s)' % \
          (self.siteInfo.name, self.siteInfo.id)
  
        retval = [uid for uid in smg.getUsers() 
                    if self.acl_users.getUser(uid)]
        assert type(retval) == list
        types = [type(u) == str for u in retval]
        assert reduce(lambda a, b: a and b, types, True), \
          u'Not all strings returned'
        return retval
        
    @Lazy
    def members(self):
        assert self.context
        siteMemberGroupIds = self.get_site_member_group_user_ids()
        retval = [createObject('groupserver.UserFromId', self.context, uid)
                   for uid in siteMemberGroupIds]
        assert type(retval) == list
        return retval

