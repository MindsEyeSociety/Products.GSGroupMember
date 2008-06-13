# coding=utf-8
"""Interfaces for the registration and password-reset pages."""
import re, pytz
from zope.interface.interface import Interface, Invalid, invariant
from zope.schema import *
from zope.schema.vocabulary import SimpleVocabulary
from zope.contentprovider.interfaces import IContentProvider
from zope.component import createObject

class IGSInviteSiteMembers(Interface):
    nonGroupMembers = List(title=u'Non Group Members',
      description=u'Members this site that are not members of this group.',
      required=True,
      value_type=Choice(title=u'Members', vocabulary='SiteMemberNonGroupMember'),
      unique=True,
      default=[])

