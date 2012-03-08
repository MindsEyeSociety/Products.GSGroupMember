# coding=utf-8
from zope.cachedescriptors.property import Lazy
from zope.interface import implements, providedBy
from zope.component import createObject
from zope.schema.vocabulary import SimpleTerm
from zope.schema.interfaces import IVocabulary, \
  IVocabularyTokenized, ITitledTokenizedTerm
from zope.interface.common.mapping import IEnumerableMapping 
from gs.profile.email.base.emailuser import EmailUser
from sitemember import SiteMembers

import logging
log = logging.getLogger('SiteMemberNonGroupMembers') #@UndefinedVariable

class SiteMembersNonGroupMembers(object):
    implements(IVocabulary, IVocabularyTokenized)
    __used_for__ = IEnumerableMapping

    def __init__(self, context):
        self.context = context
                
    @Lazy
    def acl_users(self):
        sr = self.context.site_root()
        retval = sr.acl_users
        assert retval, 'No ACL Users'
        return retval

    @Lazy
    def siteInfo(self):
        retval = createObject('groupserver.SiteInfo', self.context)
        return retval
    
    @Lazy
    def groupsInfo(self):
        retval = createObject('groupserver.GroupsInfo', self.context)
        return retval
    
    @Lazy
    def groupInfo(self):
        retval = createObject('groupserver.GroupInfo', self.context)
        return retval
        
    @Lazy
    def siteMembers(self):
        return SiteMembers(self.context)

    @Lazy
    def nonMembers(self):
        '''Get the members of the current site that are not a member of
        the group, and who have an email address.'''
        groupMemberGroupId = '%s_member' % self.groupInfo.id
        retval = [ui for ui in self.siteMembers.members
                    if ((groupMemberGroupId not in 
                            self.acl_users.getUser(ui.id).getGroups())
                        and (EmailUser(self.context, ui).get_addresses()))]
        assert type(retval) == list
        return retval

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

