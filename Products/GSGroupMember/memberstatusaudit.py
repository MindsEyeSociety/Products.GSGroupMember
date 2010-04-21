# coding=utf-8
from pytz import UTC
from datetime import datetime
from zope.component import createObject
from zope.component.interfaces import IFactory
from zope.interface import implements, implementedBy
from Products.XWFCore.XWFUtils import munge_date
from Products.CustomUserFolder.userinfo import userInfo_to_anchor
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.GSAuditTrail import IAuditEvent, BasicAuditEvent, AuditQuery
from Products.GSAuditTrail.utils import event_id_from_data

SUBSYSTEM = 'groupserver.GSGroupMemberStatus'
import logging
log = logging.getLogger(SUBSYSTEM) #@UndefinedVariable

UNKNOWN        = '0'  # Unknown is always "0"
GAIN           = '1'
LOSE           = '2'

class StatusAuditEventFactory(object):
    """A Factory for member status events.
    """
    implements(IFactory)

    title=u'GroupServer Group Status Audit Event Factory'
    description=u'Creates a GroupServer event auditor for group status changes'

    def __call__(self, context, event_id, code, date,
        userInfo, instanceUserInfo, siteInfo, groupInfo,
        instanceDatum='', supplementaryDatum='', subsystem=''):
        """Create an event
        """
        assert subsystem == SUBSYSTEM, 'Subsystems do not match'
        
        if (code == GAIN):
            event = GainStatusEvent(context, event_id, date, 
              userInfo, instanceUserInfo, siteInfo, groupInfo, 
              instanceDatum)
        elif (code == LOSE):
            event = LoseStatusEvent(context, event_id, date, 
              userInfo, instanceUserInfo, siteInfo, groupInfo, 
              instanceDatum)
        else:
            event = BasicAuditEvent(context, event_id, UNKNOWN, date, 
              userInfo, instanceUserInfo, siteInfo, groupInfo, 
              instanceDatum, supplementaryDatum, SUBSYSTEM)
        assert event
        return event
    
    def getInterfaces(self):
        return implementedBy(BasicAuditEvent)

class GainStatusEvent(BasicAuditEvent):
    ''' An audit-trail event representing a group member gaining a 
        particular status within the group
    '''
    implements(IAuditEvent)

    def __init__(self, context, id, d, userInfo, instanceUserInfo, 
                  siteInfo, groupInfo, instanceDatum):
        """ Create a gain-status event
        """
        BasicAuditEvent.__init__(self, context, id,  GAIN, d, userInfo,
          instanceUserInfo, siteInfo, groupInfo, instanceDatum, None, 
          SUBSYSTEM)
          
    def __str__(self):
        retval = u'%s (%s) gave %s (%s) the status of %s in %s (%s) on %s (%s).' % \
           (self.userInfo.name,         self.userInfo.id,
            self.instanceUserInfo.name, self.instanceUserInfo.id,
            self.instanceDatum,
            self.groupInfo.name,        self.groupInfo.id,
            self.siteInfo.name,         self.siteInfo.id)
        return retval
    
    @property
    def xhtml(self):
        cssClass = u'audit-event groupserver-group-member-%s' %\
          self.code
        retval = u'<span class="%s">Given the status of %s in %s</span>'%\
          (cssClass, self.instanceDatum, self.groupInfo.name)
        
        if self.instanceUserInfo.id != self.userInfo.id:
            retval = u'%s &#8212; %s' %\
              (retval, userInfo_to_anchor(self.userInfo))              
        retval = u'%s (%s)' % \
          (retval, munge_date(self.context, self.date))
        return retval

class LoseStatusEvent(BasicAuditEvent):
    ''' An audit-trail event representing a group member losing a 
        particular status within a group
    '''
    implements(IAuditEvent)

    def __init__(self, context, id, d, userInfo, instanceUserInfo, 
                  siteInfo, groupInfo, instanceDatum):
        """ Create a lose-status event
        """
        BasicAuditEvent.__init__(self, context, id,  LOSE, d, userInfo,
          instanceUserInfo, siteInfo, groupInfo, instanceDatum, None, 
          SUBSYSTEM)
          
    def __str__(self):
        retval = u'%s (%s) removed the status of %s from %s (%s) '\
          u'in %s (%s) on %s (%s).' %\
           (self.userInfo.name,         self.userInfo.id,
            self.instanceDatum,
            self.instanceUserInfo.name, self.instanceUserInfo.id,
            self.groupInfo.name,        self.groupInfo.id,
            self.siteInfo.name,         self.siteInfo.id)
        return retval
    
    @property
    def xhtml(self):
        cssClass = u'audit-event groupserver-group-member-%s' %\
          self.code
        retval = u'<span class="%s">Rescinded status of %s in %s</span>'%\
          (cssClass, self.instanceDatum, self.groupInfo.name)
        
        if self.instanceUserInfo.id != self.userInfo.id:
            retval = u'%s &#8212; %s' %\
              (retval, userInfo_to_anchor(self.userInfo))              
        retval = u'%s (%s)' % \
          (retval, munge_date(self.context, self.date))
        return retval

class StatusAuditor(object):
    """An auditor for group status.
    """
    def __init__(self, context, instanceUserInfo):
        """Create a status auditor.
        """
        self.context = context
        self.instanceUserInfo = instanceUserInfo
        self.__userInfo = None
        self.__siteInfo = None
        self.__groupInfo = None
        self.__factory = None
        self.__queries = None
    
    @property
    def userInfo(self):
        if self.__userInfo == None:
            self.__userInfo =\
              createObject('groupserver.LoggedInUser', self.context)
        return self.__userInfo
        
    @property
    def siteInfo(self):
        if self.__siteInfo == None:
            self.__siteInfo =\
              createObject('groupserver.SiteInfo', self.context)
        return self.__siteInfo
        
    @property
    def groupInfo(self):
        if self.__groupInfo == None:
            self.__groupInfo =\
              createObject('groupserver.GroupInfo', self.context)
        return self.__groupInfo
        
    @property
    def factory(self):
        if self.__factory == None:
            self.__factory = StatusAuditEventFactory()
        return self.__factory
        
    @property
    def queries(self):
        if self.__queries == None:
            self.__queries = AuditQuery(self.context.zsqlalchemy)
        return self.__queries
        
    def info(self, code, instanceDatum='', supplementaryDatum=''):
        """Log an info event to the audit trail.
            * Creates an ID for the new event,
            * Writes the instantiated event to the audit-table, and
            * Writes the event to the standard Python log.
        """
        d = datetime.now(UTC)
        eventId = event_id_from_data(self.userInfo, 
          self.instanceUserInfo, self.siteInfo, code, instanceDatum,
          '%s-%s' % (self.groupInfo.name, self.groupInfo.id))
          
        e = self.factory(self.context, eventId,  code, d,
          self.userInfo, self.instanceUserInfo, self.siteInfo, 
          self.groupInfo, instanceDatum, None, SUBSYSTEM)
          
        self.queries.store(e)
        log.info(e)
        return e

