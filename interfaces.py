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
                      vocabulary='groupserver.InviteMembersNonGroupMembers'),
      unique=True,
      required=True)

class IGSPostingUser(Interface):
    canPost = Bool(title=u'Can Post',
      description=u'Can the user post the the group?',
      required=True)
      
    statusNum = Int(title=u'Status Number',
      description=u'The reason the user cannot post to the group, as '\
        u'a number. 0 if the user can post.',
      required=True)
      
    status = Text(title=u'Status',
      description=u'The reason the user cannot post to the group, as '\
        u'a textual description.',)

class IGSUserCanPostContentProvider(IContentProvider):
    """The content provider for the context menu"""
    
    statusNum = Int(title=u"Status Number",
      description=u"The status number returned by the code that "\
        u"determined if the user could post.",
      required=False,
      default=0)
      
    status = Text(title=u"Posting Status",
      description=u'The posting status of the user.',
      required=False,
      default=u"")
    
    pageTemplateFileName = Text(title=u"Page Template File Name",
      description=u'The name of the ZPT file that is used to render the '\
        u'status message.',
      required=False,
      default=u"browser/templates/canpost.pt")

