# coding=utf-8
"""Interfaces for the registration and password-reset pages."""
from zope.interface.interface import Interface
from zope.interface import Attribute
from zope.schema import Bool, Choice, Int, List, Text, TextLine
from zope.contentprovider.interfaces import IContentProvider

class IGSInvitationGroups(Interface):
    invitation_groups = List(title=u'Invitation Groups',
      description=u'The groups to invite to user to. The user is not a '\
        u'member of any of these groups, but you are an administrator of '\
        u'these groups.',
      value_type=Choice(title=u'Group',
                        vocabulary='groupserver.InvitationGroups'),
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
    
class IGSGroupMembersInfo(Interface):
    mlistInfo = Attribute("""A mailingListInfo instance""")
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    members = Attribute("""All the members of the group, including invited members """\
                        """and those with no verified email addresses""")
    fullMembers = Attribute("""The members, excluding those who have been sent an """\
                            """invitation but neither declined nor accepted""")
    fullMemberCount = Attribute("""The number of members, excluding those who have """\
                                """been sent an invitation but neither declined nor accepted""")
    invitedMembers = Attribute("""The members who have been invited to the group, """\
                               """but neither declined nor accepted""")
    invitedMemberCount = Attribute("""The number of members who have been invited to """\
                                   """the group, but neither declined nor accepted""")
    ptnCoach = Attribute("""A userInfo instance""")
    groupAdmins = Attribute("""A list of userInfo instances""")
    siteAdmins = Attribute("""A list of userInfo instances""")
    moderators = Attribute("""A list of userInfo instances""")
    moderatees = Attribute("""A list of userInfo instances""")
    blockedMembers = Attribute("""A list of userInfo instances""")
    postingMembers = Attribute("""A list of userInfo instances""")
    unverifiedMembers = Attribute("""A list of userInfo instances""")
    managers = Attribute("""A list of userInfo instances""")

class IGSGroupMembershipStatus(Interface):
    userInfo = Attribute("""A userInfo instance""")
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    membersInfo = Attribute("""An IGSGroupMembersInfo instance""")
        
    status_label = TextLine(title=u'Status',
      description=u'A textual description of the user\'s status '\
      u'within the group',
      required=True)
    isNormalMember = Bool(title=u'Is Normal',
      description=u'Is the member boring in every way?',
      required=True)
    isOddlyConfigured = Bool(title=u'Is Oddly Configured',
      description=u'Does the member hold some conflicting positions?',
      required=True)
    isSiteAdmin = Bool(title=u'Is Site Administrator',
      description=u'Is the member an administrator of the site?',
      required=True)
    isGroupAdmin = Bool(title=u'Is Group Administrator',
      description=u'Is the member an administrator of the group?',
      required=True)
    isPtnCoach = Bool(title=u'Is Participation Coach',
      description=u'Is the member the participation coach of the group?',
      required=True)
    isPostingMember = Bool(title=u'Is Posting Member',
      description=u'Is the member allowed to make posts to the group?',
      required=True)
    isModerator = Bool(title=u'Is Moderator',
      description=u'Is the member a moderator of the group?',
      required=True)
    isModerated = Bool(title=u'Is Moderated',
      description=u'Are the member\s posts subject to approval '\
        u'from a moderator?',
      required=True)
    isBlocked = Bool(title=u'Is Blocked',
      description=u'Is the member blocked from posting to the group?',
      required=True)
    isInvited = Bool(title=u'Is Invited',
      description=u'Has the member been invited to the group, but '\
        u'not yet accepted or declined the invitation?',
      required=True)
    isFullMember = Bool(title=u'Is Full Member',
      description=u'Is the user a full member of the group?',
      required=True)
    isMember = Bool(title=u'Is Member',
      description=u'Is the user a member of the group, whether full or invited?',
      required=True)
    isUnverified = Bool(title=u'Is Unverified',
      description=u'Does the member have no verified email addresses?',
      required=True)
    groupIsModerated = Bool(title=u'Group is Moderated',
      description=u'Is the group moderated?',
      required=True)
    postingIsSpecial = Bool(title=u'Posting is Special',
      description=u'Is posting privileged in this group?',
      required=True)
    numPostingMembers = Int(title=u'Number of Posting Members',
      description=u'The number of posting members in this group',
      required=False)
    
    
