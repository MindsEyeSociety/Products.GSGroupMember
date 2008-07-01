# coding=utf-8
"""Interfaces for the registration and password-reset pages."""
import re, pytz
from zope.interface.interface import Interface, Invalid, invariant
from zope.schema import *
from zope.schema.vocabulary import SimpleVocabulary
from zope.contentprovider.interfaces import IContentProvider
from zope.component import createObject

class IGSInvitationGroups(Interface):
    invitation_groups = List(title=u'Invitation Groups',
      description=u'The groups to invite to user to. The user is not a '\
        u'member of any of these groups, but you are an admistrator of '\
        u'these groups.',
      value_type=Choice(title=u'Group',
                        vocabulary='groupserver.InvitationGroups'),
      unique=True,
      required=True)

class IGSInviteSiteMembers(Interface):
    site_members = List(title=u'Site Members',
      description=u'The members of this site that are not a member of '\
        u'this group.',
      value_type=Choice(title=u'Group',
                        vocabulary='groupserver.SiteMembersNonGroupMembers'),
      unique=True,
      required=True)


