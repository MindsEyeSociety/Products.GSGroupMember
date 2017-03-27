# coding=utf-8
# TODO: Move to gs.group.member.base
from zope.cachedescriptors.property import Lazy
from zope.component import createObject
from zope.interface import implements
from Products.XWFCore.XWFUtils import sort_by_name
from gs.profile.email.base.emailuser import EmailUser
from groupmembership import GroupMembers, InvitedGroupMembers
from interfaces import IGSGroupMembersInfo

import logging
log = logging.getLogger('GSGroupMembersInfo')


class GSGroupMembersInfo(object):
    implements(IGSGroupMembersInfo)

    def __init__(self, group):
        self.context = self.group = group
        assert self.context

    @Lazy
    def mlistInfo(self):
        retval = createObject('groupserver.MailingListInfo', self.group)
        return retval

    @Lazy
    def groupInfo(self):
        retval = self.mlistInfo.groupInfo
        return retval

    @Lazy
    def siteInfo(self):
        retval = createObject('groupserver.SiteInfo', self.group)
        return retval

    # TODO: Add a "normalMembers" property (full members - ptnCoach - admin)

    @Lazy
    def groupMembers(self):
        retval = GroupMembers(self.context)
        return retval

    @Lazy
    def sortedMembers(self):
        retval = self.fullMembers
        retval.sort(sort_by_name)
        return retval

    @Lazy
    def fullMembers(self):
        members = self.groupMembers.members
        return members

    @property
    def fullMemberCount(self):
        retval = len(self.groupMembers)
        return retval

    @Lazy
    def invitedMembers(self):
        retval = InvitedGroupMembers(self.context, self.siteInfo).members
        return retval

    @property
    def invitedMemberCount(self):
        return len(self.invitedMembers)

    @Lazy
    def members(self):
        allMembers = self.fullMembers + self.invitedMembers
        d = {}
        for member in allMembers:
            d[member.id] = member
        retval = d.values()
        return retval

    @Lazy
    def memberIds(self):
        retval = [m.id for m in self.members]
        return retval

    @Lazy
    def ptnCoach(self):
        ptnCoachId = self.groupInfo.get_property('ptn_coach_id', '')
        retval = None
        if ptnCoachId and (ptnCoachId in self.memberIds):
            retval = createObject('groupserver.UserFromId',
                                  self.context, ptnCoachId)
        return retval

    @Lazy
    def groupAdmins(self):
        admins = self.group.users_with_local_role('GroupAdmin')
        retval = [createObject('groupserver.UserFromId', self.context, aId)
                    for aId in admins if aId in self.memberIds]
        return retval

    @Lazy
    def siteAdmins(self):
        admins = self.siteInfo.site_admins
        retval = [a for a in admins if a.id in self.memberIds]
        return retval

    @Lazy
    def moderators(self):
        retval = []
        if self.mlistInfo.is_moderated:
            moderatorIds = self.mlistInfo.get_property('moderator_members') \
                or []
            for uId in moderatorIds:
                if uId not in self.memberIds:
                    m = u'The user ID %s is listed as a moderator for '\
                      u'the group %s (%s) on the site %s (%s), but is '\
                      u'not a member of the group.' %\
                      (uId, self.groupInfo.name, self.groupInfo.id,
                       self.siteInfo.name, self.siteInfo.id)
                    m = m.encode('ascii', 'ignore')
                    log.warn(m)
                else:
                    retval.append(createObject('groupserver.UserFromId',
                                                   self.context, uId))
        return retval

    @Lazy
    def moderatees(self):
        retval = []
        if self.mlistInfo.is_moderated:
            moderatedIds = self.mlistInfo.get_property('moderated_members') \
                or []
            if moderatedIds:
                for uId in moderatedIds:
                    if uId not in self.memberIds:
                        m = u'The user ID %s is listed as a moderated member '\
                          u'in the group %s (%s) on the site %s (%s), but is '\
                          u'not a member of the group.' %\
                          (uId, self.groupInfo.name, self.groupInfo.id,
                           self.siteInfo.name, self.siteInfo.id)
                        m = m.encode('ascii', 'ignore')
                        log.warn(m)
                    else:
                        retval.append(createObject('groupserver.UserFromId',
                                                       self.context, uId))
            #We do not want to moderate all members if no members are moderated
            #elif not(self.mlistInfo.is_moderate_new):
            #    for u in self.fullMembers:
            #        isPtnCoach = self.ptnCoach and (self.ptnCoach.id == u.id)\
            #            or False
            #        isGrpAdmin = u.id in [a.id for a in self.groupAdmins]
            #        isSiteAdmin = u.id in [a.id for a in self.siteAdmins]
            #        isModerator = u.id in [m.id for m in self.moderators]
            #        isBlocked = u.id in [m.id for m in self.blockedMembers]
            #        if (not(isSiteAdmin) and not(isGrpAdmin) and
            #            not(isPtnCoach) and not(isModerator) and
            #            not(isBlocked)):
            #            retval.append(u)
        return retval

    @Lazy
    def blockedMembers(self):
        blockedIds = self.mlistInfo.get_property('blocked_members') or []
        retval = [createObject('groupserver.UserFromId', self.context, uid)
                    for uid in blockedIds]
        return retval

    @Lazy
    def postingMembers(self):
        retval = self.fullMembers
        postingIds = self.mlistInfo.get_property('posting_members') or []
        if postingIds:
            posters = []
            for uId in postingIds:
                if uId not in self.memberIds:
                    m = u'The user ID %s is listed as a posting member '\
                      u'in the group %s (%s) on the site %s (%s), but '\
                      u'is not a member of the group.' %\
                      (uId, self.groupInfo.name, self.groupInfo.id,
                       self.siteInfo.name, self.siteInfo.id)
                    m = m.encode('ascii', 'ignore')
                    log.warn(m)
                else:
                    posters.append(createObject('groupserver.UserFromId',
                                                self.context, uId))
                posters.sort(sort_by_name)
                retval = posters
        return retval

    @Lazy
    def unverifiedMembers(self):
        emailUsers = [EmailUser(self.context, m) for m in self.members]
        members = [e.userInfo for e in emailUsers
                  if not(e.get_verified_addresses())]
        retval = members
        return retval

    @Lazy
    def managers(self):
        admins = self.groupAdmins + self.siteAdmins
        groupAdminIds = set([a.id for a in self.groupAdmins])
        siteAdminIds = set([a.id for a in self.siteAdmins])
        distinctAdminIds = groupAdminIds.union(siteAdminIds)
        retval = []
        for uId in distinctAdminIds:
            admin = [a for a in admins if a.id == uId][0]
            retval.append(admin)
        return retval
