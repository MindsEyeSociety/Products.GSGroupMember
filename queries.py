# coding=utf-8
from sqlalchemy.exceptions import NoSuchTableError
import sqlalchemy as sa
import pytz, datetime

import logging
log = logging.getLogger("GroupMemberQuery")

class GroupMemberQuery(object):
    def __init__(self, context, da):
        self.context = context

        engine = da.engine
        metadata = sa.BoundMetaData(engine)
        self.userInvitation = sa.Table('user_invitation', metadata, 
          autoload=True)

    def add_invitation(self, invitiationId, siteId, groupId, userId, invtUsrId):
        assert invitiationId
        assert siteId
        assert groupId
        assert userId
        assert invtUsrId
        
        d = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        i = self.userInvitation.insert()
        i.execute(invitiation_id = invitationId,
          site_id = siteId,
          group_id = groupId,
          user_id = userId,
          inviting_user_id = invtUsrId,
          invitation_date = d)
    
    def get_current_invitiations(self, siteId, groupId, userId):
        assert siteId
        assert groupId
        assert userId
        
        uit = self.userInvitation
        cols = [
          uit.c.site_id, uit.c.group_id, uit.c.user_id, 
          uit.c.inviting_user_id, uit.c.invitiation_date]
        s = uit.select(cols, distinct=True)
        s.append_whereclause(uit.c.site_id  == siteId)
        s.append_whereclause(uit.c.group_id == groupId)
        s.append_whereclause(uit.c.user_id  == userId)
        s.append_whereclause(uit.c.response_date == None)
        
        r = s.execute()
        
        retval = []
        if r.rowcount:
            retval = {
              'site_id',          x['site_id'],
              'group_id',         x['group_id'],
              'user_id',          x['user_id'],
              'inviting_user_id', x['inviting_user_id'],
              'invitation_date',  x['invitation_date']} for x in r]

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
        uit = self.userInvitation
        c = sa.and_(
          uit.c.site_id  == siteId, 
          uit.c.group_id == groupId,
          uit.c.user_id  == userid)
        u = uit.update(c)
        u.execute(uit.c.response_date = d, uit.c.accepted = status)

