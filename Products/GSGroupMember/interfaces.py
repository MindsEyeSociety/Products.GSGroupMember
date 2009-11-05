# coding=utf-8
"""Interfaces for the registration and password-reset pages."""
from zope.interface.interface import Interface
from zope.interface import Attribute
from zope.schema import *
from zope.contentprovider.interfaces import IContentProvider
from Products.GSProfile.interfaces import deliveryVocab

class IGSInvitationGroups(Interface):
    invitation_groups = List(title=u'Invitation Groups',
      description=u'The groups to invite to user to. The user is not a '\
        u'member of any of these groups, but you are an administrator of '\
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

    delivery = Choice(title=u'Group Message Delivery Settings',
      description=u'The message delivery settings for the new group '\
        u'members.',
      vocabulary=deliveryVocab,
      default='email')

class IGSJoinGroup(Interface):
    delivery = Choice(title=u'Message Delivery Settings',
      description=u'Your message delivery settings.',
      vocabulary=deliveryVocab,
      default='email')

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

class IGSManageGroupMembersForm(Interface):
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    memberManager = Attribute("""A GSGroupMemberManager instance""")
    # Form fields will be taken from memberManager.form_fields
    form_fields = Attribute("""The fields to be displayed in a form""")
    
class IGSGroupMemberManager(Interface):
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    membersInfo = Attribute("""A GSGroupMembersInfo instance""")
    memberStatusActions = Attribute("""A list of GSMemberStatusActions instances""")
    # Form fields will be gathered user-by-user, from memberStatusActions 
    form_fields = Attribute("""The fields to be displayed in a form""") 
    
class IGSGroupMembersInfo(Interface):
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
    
class IGSMemberStatusActions(Interface):
    userInfo = Attribute("""A userInfo instance""")
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    status = Attribute("""A GSGroupMembershipStatus instance""")
    form_fields = Attribute("""The fields to be displayed in a form to change """\
                            """the membership status of this user""")

class IGSGroupMembershipStatus(Interface):
    userInfo = Attribute("""A userInfo instance""")
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
        
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
    
class IGSStatusFormFields(Interface):
    """ An adapter to take a member's status within a group, and
        give us the appropriate form_fields to alter the status,
        also depending on the status of the logged-in administrator.
    """
    status = Attribute("""A GSGroupMembershipStatus instance""")
    userInfo = Attribute("""A userInfo instance""")
    groupInfo = Attribute("""A groupInfo instance""")
    siteInfo = Attribute("""A siteInfo instance""")
    
    adminUserInfo = Attribute("""A userInfo instance for the logged-in administrator""")
    adminUserStatus = Attribute("""A GSGroupMembershipStatus instance for the logged-in administrator""")
    
    form_fields = Attribute("""The fields to be displayed in a form to change """\
                            """the membership status of this user""")

    groupAdmin = Bool(title=u'Make fn a Group Administrator (or Unmake)',
      description=u'Make fn a Group Administrator (or Unmake)',
      required=False)
    ptnCoach = Bool(title=u'Make fn the Participation Coach (or Unmake)',
      description=u'Make fn the Participation Coach (or Unmake)',
      required=False)
    moderator = Bool(title=u'Make fn a Moderator (or Unmake)',
      description=u'Make fn a Moderator (or Unmake)',
      required=False)
    moderate = Bool(title=u'Moderate fn (or Unmoderate)',
      description=u'Moderate fn (or Unmoderate)',
      required=False)
    postingMember = Bool(title=u'Make fn a Posting Member (or Unmake)',
      description=u'Make fn a Posting Member (or Unmake)',
      required=False)
    remove = Bool(title=u'Remove fn from the Group',
      description=u'Remove fn from the Group',
      required=False)
    
class IGSMemberStatusActionsContentProvider(Interface):
    """The content provider for the actions available to change """\
    """a group member's status within the group"""
    
    #statusActions = Attribute("""A GSMemberStatusActions instance""")
    statusActions = List(title=u'Instances',
      description=u'GSMemberStatusActions instances',
      required=True)
    
    widgets = List(title=u'Widgets',
      description=u'Form Widgets',
      required=True)
    
    pageTemplateFileName = Text(title=u"Page Template File Name",
      description=u'The name of the ZPT file that is used to render the '\
        u'group member\'s status and the appropriate form widgets.',
      required=False,
      default=u"browser/templates/statusActionsContentProvider.pt") 
    
class IGSMemberActionsSchema(Interface):
    """ Dummy interface to get the schema started.
    """
    dummy = Bool(title=u'Dummy',
      description=u'Is this a dummy value?',
      required=False)
        
