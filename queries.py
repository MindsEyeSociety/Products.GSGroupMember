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
        self.userInvitationTable = sa.Table('user_invitation', metadata, 
          autoload=True)

    def add_invitation(self, invitiationId, siteId, groupId, userId, invtUsrId):
        assert invitiationId
        assert siteId
        assert groupId
        assert userId
        assert invtUsrId
        
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        i = self.userInvitationTable.insert()
        i.execute(invitiation_id = invitationId,
          site_id = siteId,
          group_id = groupId,
          user_id = userId,
          inviting_user_id = invtUsrId,
          invitation_date = d)
    
    def get_current_invitiations_for_site(self, siteId, userId):
        assert siteId
        assert userId
        uit = self.userInvitationTable
        cols = [uit.c.site_id, uit.c.group_id, uit.c.user_id, 
                uit.c.inviting_user_id, uit.c.invitation_date]
        s = sa.select(cols, distinct=True)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.user_id  == userId)
        s.append_whereclause(uit.c.response_date == None)
        s.order_by(sa.desc(uit.c.invitation_date))

        r = s.execute()

        retval = []
        if r.rowcount:
            retval = [{
              'site_id':          x['site_id'],
              'group_id':         x['group_id'],
              'user_id':          x['user_id'],
              'inviting_user_id': x['inviting_user_id'],
              'invitation_date':  x['invitation_date']} for x in r]

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
          uit.c.user_id  == userid)
        v = {uit.c.response_date: d, uit.c.accepted: status}
        u = uit.update(c, values=v)
        u.execute()        

