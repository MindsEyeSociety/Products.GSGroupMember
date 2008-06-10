from zope.interface.interface import Interface
from zope.schema import *

import sqlalchemy as sa
import datetime, pytz, time, md5

from Products.CustomUserFolder.interfaces import ICustomUser
from Products.GSContent.interfaces import IGSGroupInfo
from Products.XWFCore import XWFUtils

import logging
log = logging.getLogger('GSGroupMember.invitedgroupmember')

class IGSInvitedGroupMember(Interface):
    group = Field(title=u'Group',
      description=u'The group the user is being invited to join',
      required=True)

    user = Field(title=u'User',
      description=u'The user that is being invited to join the group',
      required=True)

    hasInvitation = Bool(title=u'Has Invitation',
      description=u'Does the user have an invitation to join the group?',
      required=True)
      
    isMember = Bool(title=u'Is Member',
      description=u'Is the user already a member of the group?',
      required = True)

    def add_invitation():
        '''Invite the user to join the group.
        
        DESCRIPTION
            Add an invitation to the user, inviting the user to join the
            group.

        RETURNS
            A unicode string describing the success.
        
        SIDE EFFECTS
            A notification is sent to the user, inviting the member to
            join the group.
        '''
    def remove_invitations():
        '''Remove all invitations, inviting the user to join the group.
        
        DESCRIPTION
            Remove all invitations, for the user to join the group.
            
        RETURNS
            A unicode string describing the success.
            
        SIDE EFFECTS
            All invitations, relating to the user joining the group, are
            removed from the store.
        '''
    def decline_invitation():
        '''Decline the invitation to join the group.
        
        DESCRIPTION
            Decline the invitation to join the group. This is called by
            the user, and is different from "remove_invitation".
        
        RETURNS
            A unicode string describing the success.
        
        SIDE EFFECTS
            * All invitations, inviting the user to join the group, are
              removed from the store.
        '''
        
    def accept_invitation():
        '''Accept the invitation to join the group.
        
        DESCRIPTION
            Accept the invitation to join the group.

        RETURNS
            A unicode string describing the success.
        
        SIDE EFFECTS
            * All invitations, inviting the user to join the group, are
              removed from the store.
            * The user recieves a welcome notifcation.
            * The user becomes a member of the group.
        '''

class ExistingMember(Exception):
    '''The user is already a member of the group
    '''
    pass

class NoInvitation(Exception):
    '''No invitation exists, inviting the user to join the group'''
    pass

class InvitationQuery(object):
    def __init__(self, da):
        self.invitationTable = sa.Table('user_invitation', 
          sa.BoundMetaData(da.engne), autoload=True)
          
    def pending_invitations(self, userId, siteId, groupId):
        assert userId
        assert siteId
        assert groupId
        
        it = self.invitationTable
        statement = it.select()
        statement.append_whereclause(it.c.user_id == userId)
        statement.append_whereclause(it.c.site_id == siteId)
        statement.append_whereclause(it.c.group_id == groupId)
        statement.append_whereclause(it.c.response_date == None)
        
        r = statement.execute()
        retval = []
        for row in r.fetchall():
            retval.append({
              'invitation_id': row['invitation_id'],
              'inviting_user_id': row['inviting_user_id'],
              'invitation_date':  row['invitation_date'],
            })
        assert type(retval) == list
        
    def add_invitation(self, invitationId, userId, invitingUserId, siteId, groupId):
        assert invitationId
        assert userId
        assert invitingUserId
        assert siteId
        assert groupId

        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        
        it = self.invitationTable
        i = it.insert()
        i.execute(
          invitation_id = invitationId, 
          user_id = userId,
          inviting_user_id = invitingUserId,
          site_id = siteId,
          group_id = groupId,
          invitation_date = d,
          response_date = None,
          accepted = False)

    def remove_invitations(self, userId, siteId, groupId):
        assert userId
        assert siteId
        assert groupId
        
        it = self.invitationTable
        d = it.delete(sa.and_(it.c.user_id == userId, 
              it.c.site_id == siteId,
              it.c.group_id == groupId))
        d.execute()

    def alter_invitations(self, userId, siteId, groupId, values):
        clause = sa.and_(it.c.userId == userID, 
          it.c.siteId == siteId,
          it.c.groupId == groupId)

        it = self.invitationTable
        u = it.update(clause, values=values)
        u.execute()

    def accept_invitations(self, userId, siteId, groupId):
        assert userId
        assert siteId
        assert groupId
        
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        values = {
          'response_date':  d,
          'accepted':       True,
        }
        self.alter_invitations(userId, siteId, groupId, values)

    def reject_invitations(self, userId, siteId, groupId):
        assert userId
        assert siteId
        assert groupId
        
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        values = {
          'response_date':  d,
          'accepted':       False,
        }
        self.alter_invitations(userId, siteId, groupId, values)
        
class TooManyInvitations(Exception):
    '''Too many invitation exists, so the user cannot be invited to
       join the group'''
    def __init__(self, userInfo, groupInfo):
        self.userInfo = userInfo
        self.groupInfo = groupInfo
        Exception.__init__(self)
    def __str__(self):
        retval = u'There are too many invitations for %s to %s.' %\
          (self.userInfo.name, self.groupInfo.name)
        assert type(retval) == unicode
        return retval

class GSInvitedGroupMember:
    implements(IGSInvitedGroupMember)
    adapts(IGSCustomUser, IGSGroupInfo)

    MAX_INVITATIONS = 5

    def __init__(self, userInfo, groupInfo):
        self.userInfo = userInfo
        self.groupInfo = groupInfo
        self.siteInfo = groupInfo.siteInfo
        
        da = self.groupInfo.groupObj.zsqlalchemy
        self.queries = InvitationQuery(da)
        
    @property
    def invitations(self):
        '''Get the invitations for the user to the group
        '''
        uid = self.userInfo.id
        sid = self.siteInfo.id
        gid = self.groupInfo.id
        retval = self.queries.pending_invitations(uid, sid, gid)
        
        if len(retval) >= MAX_INVITATIONS:
            m = u'%s (%s) has %d invitations to %s (%s) on %s (%s)' %\
              (self.userInfo.name, self.userInfo.id,
               len(retval),
               self.groupInfo.name, self.groupInfo.id,
               self.siteInfo.name, self.siteInfo.id)
            log.warn(m)
        assert type(retval) == list
        return retval

    @property
    def hasInvitation(self):
        retval = self.invitations != []
        assert type(retval) == bool
        return retval

    @property
    def isMember(self):
        roles = self.userInfo.user.getRolesInContext(self.groupInfo.groupObj)
        retval = 'GroupMember' in roles 
        assert type(retval) == bool
        return retval

    def add_invitation(self, invitingUser, message=''):
        if len(self.invitations) >= self.MAX_INVITATIONS:
            m = u'Not adding invitation for %s (%s) on %s (%s) to %s (%s) '
              u'as there are too many invitations (%d) already.' %\
              (self.userInfo.name, self.userInfo.id, 
               self.siteInfo.name, self.siteInfo.id, 
               self.groupInfo.name, self.groupInfo.id,
               self.MAX_INVITATIONS)
            log.error(m)
            raise TooManyInvitations(self.userInfo, self.groupInfo)
    
        inviteString = time.asctime() + self.userInfo.name + \
          self.groupInfo.name + self.siteInfo.name
        inviteNum = long(md5.new(inviteString).hexdigest(), 16)
        invitationId = str(XWFUtils.convert_int2b62(inviteNum))

        self.queries.add_invitation(invitationId, self.userInfo.id,
          invitingUser.id, self.siteInfo.id, self.groupInfo.id)

        m = u'Added invitation %s to the group %s (%s) on %s (%s) for the '\
          u'user %s (%s) from %s (%s)' %\
          (invitationID,
           self.groupInfo.name, self.groupInfo.id,
           self.siteInfo.name, self.siteInfo.id, 
           self.userInfo.name, self.userInfo.id, 
           self.invitingUser.name, self.invitingUser.id)
        log.info(m)
        
        assert self.hasInvitation, u'%s (%s) has no invitations' %
          (self.userInfo.name, self.userInfo.id)
        retval = u'%s has been invited to join %s' % \
          (self.userInfo.name, self.groupInfo.name)
        assert type(retval) == unicode
        return retval

    def accept_invitation(self):
        assert not(self.isMember), '%s (%s) is already a member of %s (%s)'%\
          (self.userInfo.name, self.userInfo.id
           self.groupInfo.name, self.groupInfo.id)
           
        m = u'Accepting the invitation to the group %s (%s) for the user '\
          u'%s (%s)'%\
          (self.groupInfo.name, self.groupInfo.id,
           self.userInfo.name, self.userInfo.id)
        log.info(m)
        
        # TODO: Add to group
        
        self.queries.accept_invitations()
        
        assert self.isMember, '%s (%s) is not a member of %s (%s)' %\
          (self.userInfo.name, self.userInfo.id
           self.groupInfo.name, self.groupInfo.id)
        assert not(self.hasInvitation), '%s (%s) has invites to %s (%s)' %\
          (self.userInfo.name, self.userInfo.id
           self.groupInfo.name, self.groupInfo.id)
        retval = u'Accepting invitations is not implemented'
        assert type(retval) == unicode
        return retval

    def decline_invitation(self):
        assert not(self.isMember), '%s (%s) is already a member of %s (%s)'%\
          (self.userInfo.name, self.userInfo.id
           self.groupInfo.name, self.groupInfo.id)

        self.queries.reject_invitations()

        m = u'Declined the invitation to the group %s (%s) on %s for the '\
          u' user %s (%s). Invitation made by %s (%s)'%\
          (self.groupInfo.name, self.groupInfo.id,
           self.userInfo.name, self.userInfo.id)
        log.info(m)
        self.remove_invitations()

        assert not(self.isMember), '%s (%s) is a member of %s (%s)'%\
          (self.userInfo.name, self.userInfo.id
           self.groupInfo.name, self.groupInfo.id)

        retval = u'Declining invitations is not implemented'
        assert type(retval) == unicode
        return retval

