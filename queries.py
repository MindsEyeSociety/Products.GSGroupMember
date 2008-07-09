# coding=utf-8
from sqlalchemy.exceptions import NoSuchTableError
import sqlalchemy as sa
import pytz, datetime

import logging
log = logging.getLogger("GroupMemberQuery")

class GroupMemberQuery(object):
    def __init__(self, da):

        engine = da.engine
        metadata = sa.BoundMetaData(engine)
        self.userInvitationTable = sa.Table(
          'user_group_member_invitation', 
          metadata, 
          autoload=True)

    def add_invitation(self, invitiationId, siteId, groupId, userId, invtUsrId):
        assert invitiationId, 'invitiationId is %s' % invitiationId
        assert siteId, 'siteId is %s' % siteId
        assert groupId, 'groupId is %s' % groupId
        assert userId, 'userId is %s' % userId
        assert invtUsrId, 'invtUsrId is %s' % invtUsrId
        
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        i = self.userInvitationTable.insert()
        i.execute(invitation_id = invitiationId,
          site_id = siteId,
          group_id = groupId,
          user_id = userId,
          inviting_user_id = invtUsrId,
          invitation_date = d)

    def get_invitation(self, invitationId, current=True):
        uit = self.userInvitationTable
        cols = [uit.c.site_id, uit.c.group_id, uit.c.user_id, 
                uit.c.inviting_user_id, uit.c.invitation_date]
        s = sa.select(cols)
        s.append_whereclause(uit.c.invitation_id == invitationId)
        if current:
            s.append_whereclause(uit.c.response_date == None)
        r = s.execute()

        retval = None
        if r.rowcount:
            result = r.fetchone()
            retval = {
              'site_id':          result['site_id'],
              'group_id':         result['group_id'],
              'user_id':          result['user_id'],
              'inviting_user_id': result['inviting_user_id'],
              'invitation_date':  result['invitation_date']}
        return retval
            
    def get_current_invitiations_for_site(self, siteId, userId):
        assert siteId
        assert userId
        uit = self.userInvitationTable
        cols = [uit.c.site_id, uit.c.group_id, uit.c.user_id, 
                uit.c.inviting_user_id, 
                sa.func.max(uit.c.invitation_date).label('date')]
        s = sa.select(cols)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.user_id  == userId)
        s.append_whereclause(uit.c.response_date == None)
        s.order_by(sa.desc('date'))
        s.group_by(uit.c.site_id, uit.c.group_id, uit.c.user_id, 
            uit.c.inviting_user_id)
        r = s.execute()

        retval = []
        if r.rowcount:
            retval = [{
              'site_id':          x['site_id'],
              'group_id':         x['group_id'],
              'user_id':          x['user_id'],
              'inviting_user_id': x['inviting_user_id'],
              'invitation_date':  x['date']} for x in r]

        assert type(retval) == list
        return retval

    def get_past_invitiations_for_site(self, siteId, userId):
        assert siteId
        assert userId
        uit = self.userInvitationTable
        cols = [uit.c.site_id, uit.c.group_id, uit.c.user_id, 
                uit.c.inviting_user_id, uit.c.invitation_date,
                uit.c.response_date, uit.c.accepted]
        s = sa.select(cols, distinct=True)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.user_id  == userId)
        s.append_whereclause(uit.c.response_date != None)
        s.order_by(sa.desc(uit.c.invitation_date))

        r = s.execute()

        retval = []
        if r.rowcount:
            retval = [{
              'site_id':          x['site_id'],
              'group_id':         x['group_id'],
              'user_id':          x['user_id'],
              'inviting_user_id': x['inviting_user_id'],
              'invitation_date':  x['invitation_date'],
              'response_date':    x['response_date'],
              'accepted':         x['accepted']} for x in r]

        assert type(retval) == list
        return retval

    def get_invitations_sent_by_user(self, siteId, invitingUserId):
        assert siteId
        assert invitingUserId
        uit = self.userInvitationTable
        cols = [uit.c.site_id, uit.c.group_id, uit.c.user_id, 
                uit.c.invitation_date, uit.c.response_date, uit.c.accepted]
        s = sa.select(cols, distinct=True)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.inviting_user_id  == invitingUserId)
        s.order_by(sa.desc(uit.c.invitation_date))

        r = s.execute()

        retval = []
        if r.rowcount:
            retval = [{
              'site_id':          x['site_id'],
              'group_id':         x['group_id'],
              'user_id':          x['user_id'],
              'invitation_date':  x['invitation_date'],
              'response_date':    x['response_date'],
              'accepted':         x['accepted']} for x in r]

        assert type(retval) == list
        return retval
        
    def accept_invitation(self, siteId, groupId, userId):
        self.alter_invitation(siteId, groupId, userId, True)
        
    def decline_invitation(self, siteId, groupId, userId):
        self.alter_invitation(siteId, groupId, userId, False)
        
    def alter_invitation(self, siteId, groupId, userId, status):
        assert siteId
        assert groupId
        assert userId
        assert type(status) == bool

        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)        
        uit = self.userInvitationTable
        c = sa.and_(
          uit.c.site_id  == siteId, 
          uit.c.group_id == groupId,
          uit.c.user_id  == userId)
        v = {uit.c.response_date: d, uit.c.accepted: status}
        u = uit.update(c, values=v)
        u.execute()        

    def get_count_current_invitations_in_group(self, siteId, groupId, userId):
        uit = self.userInvitationTable
        cols = [sa.func.count(uit.c.invitation_id.distinct())]
        s = sa.select(cols)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.group_id  == groupId)
        s.append_whereclause(uit.c.user_id  == userId)
        s.append_whereclause(uit.c.response_date == None)

        r = s.execute()
        retval = r.scalar()
        if retval == None:
            retval = 0
        assert retval >= 0
        return retval

