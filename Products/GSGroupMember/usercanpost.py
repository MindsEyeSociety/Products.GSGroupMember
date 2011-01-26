# coding=utf-8
import pytz
from datetime import datetime, timedelta

from zope.app.apidoc import interface
from zope.component import createObject, adapts
from zope.interface import implements

from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.XWFChat.interfaces import IGSGroupFolder
from Products.GSGroup.interfaces import IGSGroupInfo
from Products.GSGroupMember.groupmembership import user_member_of_group,\
  user_participation_coach_of_group, user_admin_of_group 
from Products.XWFCore.XWFUtils import munge_date, timedelta_to_string, \
  comma_comma_and
from Products.GSSearch.queries import MessageQuery
from Products.GSProfile import interfaces as profileinterfaces
from gs.profile.email.base.emailuser import EmailUser
from interfaces import IGSPostingUser

#TODO Replace with an audit trail
import logging
log = logging.getLogger('GSGroupMember')

class GSGroupMemberPostingInfo(object):

    adapts(IGSGroupFolder, IGSUserInfo)
    implements(IGSPostingUser)

    def __init__(self, group, userInfo):
        assert IGSGroupFolder.providedBy(group),\
          u'%s is not a group folder' % group
        assert IGSUserInfo.providedBy(userInfo),\
          u'%s is not a user-info' % userInfo
        
        self.site_root = site_root = group.site_root()
        
        self.mailingListManager = site_root.ListManager
        self.mailingList = self.mailingListManager.get_list(group.getId())
        
        self.userInfo = userInfo
        self.groupInfo = IGSGroupInfo(group)
        
        da = site_root.zsqlalchemy 
        assert da
        self.messageQuery = MessageQuery(group, da)
        
        self.__status = None
        self.__statusNum = 0
        self.__canPost = None
        self.__profileInterfaces = None
    
    @property
    def status(self):
        if self.__status == None:
            # call self.canPost so that __status gets set as a side-effect.
            _justCall = self.canPost
        retval = self.__status
        assert retval
        assert type(retval) == unicode
        return retval

    @property
    def statusNum(self):
        retval = self.__statusNum
        assert type(retval) == int
        return retval

    @property
    def canPost(self):
        if self.__canPost == None:
            self.__canPost = \
              self.group_is_unclosed() or\
               (not(self.user_anonymous()) and\
                self.user_is_member() and\
                self.user_has_preferred_email_addresses() and\
                self.user_is_posting_member() and\
                not(self.user_posting_limit_hit()) and\
                not(self.user_blocked_from_posting()) and\
                self.user_has_required_properties())
        retval = self.__canPost
        assert type(retval) == bool
        return retval
        
    def group_is_unclosed(self):
        '''A closed group is one where only members can post. It is 
          defined by the Germanic-property "unclosed", which GroupServer
          inherited from MailBoxer. (We would love to change its name, but
          it would break too much code.)
          
          If the "unclosed" property is "True" then the group is open to 
          any poster, and we do not have to bother with any member-specific
          checks. Support groups like this.
          
          If the "unclosed" property is "False" then we have to perform the
          member-specific checks to ensure that the posting user is allowed
          to post.
        '''
        retval = self.mailingList.getProperty('unclosed', False)
        if retval:
            self.__status = u'the group is open to anyone posting'
            self.__statusNum = self.__statusNum + 0
        else:
            self.__status = u'not a member'
            self.__statusNum = 1

        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_anonymous(self):
        '''Is the user anonymous? Anonymous users are not allowed to post.
        '''
        retval = self.userInfo.anonymous
        if retval:
            self.__status = u'not logged in'
            self.__statusNum = 2
        else:
            self.__status = u'logged in'
            self.__statusNum = 0
            
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_has_preferred_email_addresses(self):
        '''Does the user have at least one preferred (alias default 
        delivery) email address to post. This is mostly a safety 
        catch to ensure that the user has verified the email addresses.
        '''
        emailUser = EmailUser(self.groupInfo.groupObj, self.userInfo)
        preferredEmailAddresses = emailUser.get_delivery_addresses()
        retval = len(preferredEmailAddresses) >= 1
        if retval:
            self.__status = u'preferred email addresses'
        else:
            self.__status = u'no preferred email addresses'
            self.__statusNum = 4
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_is_member(self):
        '''A user is a member of the group if the the user has the member
        role in the group context. While this may sound like I am stating
        the blindingly obvious, this was not always the case!
        '''
        retval = user_member_of_group(self.userInfo.user, 
                                      self.groupInfo.groupObj)
        if retval:
            self.__status = u'a member'
        else:
            self.__status = u'not a member'
            self.__statusNum = 8
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_is_posting_member(self):
        '''Check the "posting_members" property of the mailing list,
        which is assumed to be a lines-property containing the user-IDs of
        the people who can post. If the property does not contain any
        values, it is assumed that everyone is a posting member.
        '''
        postingMembers = self.mailingList.getProperty('posting_members', [])
        if postingMembers:
            retval = self.userInfo.id in postingMembers
        else:
            retval = True
        if retval:
            self.__status = u'posting member'
        else:
            self.__status = u'not a posting member'
            self.__statusNum = 16
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_posting_limit_hit(self):
        '''The posting limits are based on the *rate* of posting to the 
        group. The maximum allowed rate of posting is defined by the 
        "senderlimit" and "senderinterval" properties of the mailing list
        for the group. If the user has exceeded his or her posting limits
        if  more than "senderlimit" posts have been sent in
        "senderinterval" seconds to the group.
        '''
        if user_participation_coach_of_group(self.userInfo, self.groupInfo):
            retval = False
            self.__status = u'participation coach'
            self.__statusNum = self.__statusNum + 0
        elif user_admin_of_group(self.userInfo, self.groupInfo):
            retval = False
            self.__status = u'administrator of'
            self.__statusNum = self.__statusNum + 0
        else:
            # The user is not the participation coach or the administrator
            # of the group
            sid = self.groupInfo.siteInfo.id
            gid = self.groupInfo.id
            uid = self.userInfo.id
            limit = self.mailingList.getValueFor('senderlimit')
            interval = self.mailingList.getValueFor('senderinterval')
            td = timedelta(seconds=interval)
            now = datetime.now(pytz.utc)
            earlyDate = now - td
            count = self.messageQuery.num_posts_after_date(sid, gid, uid, 
                                                           earlyDate)
            if count >= limit:
                # The user has made over the allowed number of posts in
                # the interval
                retval = True
                d = self.old_message_post_date()
                
                canPostDate = d + td
                prettyDate = munge_date(self.groupInfo.groupObj, 
                    canPostDate, user=self.userInfo.user)
                prettyDelta = timedelta_to_string(canPostDate - now)
                self.__status = u'post again at %s\n-- in %s' %\
                  (prettyDate, prettyDelta)
                self.__statusNum = 32
            else:
                retval = False
                self.__status = u'under the posting limit'
                self.__statusNum = self.__statusNum + 0
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def old_message_post_date(self):
        sid = self.groupInfo.siteInfo.id
        gid = self.groupInfo.id
        uid = self.userInfo.id
        limit = self.mailingList.getValueFor('senderlimit')
        offset = limit - 1
        if offset < 0:
            offset = 0
            log.warning("senderlimit of %s was set to 0 or less" % gid)
            
        tokens = createObject('groupserver.SearchTextTokens', '')
        posts = self.messageQuery.post_search_keyword(tokens, sid, [gid], 
          [uid], 1, offset)
        
        assert len(posts) == 1
        retval = posts[0]['date']
        assert isinstance(retval, datetime)
        
        return retval

    def user_blocked_from_posting(self):
        '''Blocking a user from posting is a powerful, but rarely used
        tool. Rather than removing a disruptive member from the group, or
        moderating the user, the user can be blocked from posting.
        '''
        blockedMemberIds = self.mailingList.getProperty('blocked_members', 
                                                        [])
        if (self.userInfo.id in blockedMemberIds):
            retval = True
            self.__status = u'blocked from posting'
            self.__statusNum = self.__statusNum + 64
        else:
            retval = False
            self.__status = u'not blocked from posting'
            self.__statusNum = self.__statusNum + 0
        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def user_has_required_properties(self):
        '''The user must have the required properties filled out before
        he or she can post to the group — otherwise they would not be
        required, would they! The required properties can come from one
        of two places: the properties that are required for the site, and
        the properties required for the group. 
        '''
        requiredSiteProperties = self.get_required_site_properties()
        requiredGroupProperties = self.get_required_group_properties()
        requiredProperties = requiredSiteProperties + requiredGroupProperties
        
        unsetRequiredProps = [p for p in requiredProperties
                              if not(self.userInfo.get_property(p, None))]
        if unsetRequiredProps:
            retval = False
            self.__status = u'required properties set'
            fields = [a.title for n, a in self.get_site_properties() 
                      if n in unsetRequiredProps]
            f = comma_comma_and(fields)
            attr = (len(fields) == 1 and u'attribute') or u'attributes'
            isare = (len(fields) == 1 and u'is') or u'are'
            self.__status = u'required %s %s %s not set' % (attr, f, isare)
            self.__statusNum = self.__statusNum + 128
        else:
            retval = True
            self.__status = u'required properties set'

        assert type(self.__status) == unicode
        assert type(retval) == bool
        return retval

    def get_site_properties(self):
        '''Whole-heartly nicked from the GSProfile code, the site-wide
        user properties rely on a bit of voodoo: the schemas themselves
        are defined in the file-system, but which schema to use is stored
        in the "GlobalConfiguration" instance.
        '''
        if self.__profileInterfaces == None:
            assert hasattr(self.site_root, 'GlobalConfiguration')
            config = self.site_root.GlobalConfiguration
            ifName = config.getProperty('profileInterface',
                        'IGSCoreProfile')
            # --=mpj17=-- Sometimes profileInterface is set to ''
            ifName = (ifName and ifName) or 'IGSCoreProfile'
            assert hasattr(profileinterfaces, ifName), \
                'Interface "%s" not found.' % ifName
            profileInterface = getattr(profileinterfaces, ifName)
            self.__profileInterfaces =\
              interface.getFieldsInOrder(profileInterface)
        retval = self.__profileInterfaces
        return retval

    def get_required_site_properties(self):
        '''Site-properties are properties that are required to be a member
        of the site. It is very hard *not* to have required site-properties
        filled out, but as subscription-by-email is possible, we have to
        allow for the possibility.
        '''
        retval = [n for n, a in self.get_site_properties() if a.required]
        assert type(retval) == list
        return retval
        
    def get_required_group_properties(self):
        '''Required group properties are stored on the mailing-list 
        instance for the group. They are checked against the site-wide
        user properties, to ensure that it is *possible* to have the
        user-profile attribute filled.
        '''
        groupProps = self.mailingList.getProperty('required_properties', [])
        siteProps = [n for n, _a in self.get_site_properties()]
        retval = []
        for prop in groupProps:
            if prop in siteProps:
                retval.append(prop)
        assert type(retval) == list
        return retval

