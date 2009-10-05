# coding=utf-8
from pytz import UTC
from datetime import datetime
from zope.component import createObject
from zope.component.interfaces import IFactory
from zope.interface import implements, implementedBy
from Products.GSAuditTrail import IAuditEvent, BasicAuditEvent,\
  AuditQuery
from Products.GSAuditTrail.utils import event_id_from_data

SUBSYSTEM = 'groupserver.GSGroupMemberJoin'
import logging
log = logging.getLogger(SUBSYSTEM) #@UndefinedVariable

UNKNOWN        = '0'  # Unknown is always "0"
JOIN           = '1'

class JoinAuditEventFactory(object):
    """A Factory for allocation events.
    """
    implements(IFactory)

    title=u'GroupServer Join Group Audit Event Factory'
    description=u'Creates a GroupServer event auditor for joining groups'

    def __call__(self, context, event_id, code, date,
        userInfo, instanceUserInfo, siteInfo, groupInfo,
        instanceDatum='', supplementaryDatum='', subsystem=''):
        """Create an event
        
        DESCRIPTION
            The factory is called to create event instances. It
            expects all the arguments that are required to create an
            event instance, though it ignores some. The arguments to
            this method *must* be the same for *all* event
            factories, no matter the subsystem, and the argument 
            names *must* match the fields returned by the 
            getter-methods of the audit trail query.
            
        ARGUMENTS
            context
                The context used to create the event.
                
            event_id
                The identifier for the event.
                
            code
                The code used to determine the event that is 
                instantiated.
                
            date
                The date the event occurred.
                
            userInfo
                The user who caused the event.
                
            instanceUserInfo
                The user who had an event occurred to them.
                
            siteInfo
                The site where the event occurred. Always set for
                allocation events.
                
            groupInfo
                The workshop-group where the event occurred. 
                
            instanceDatum
                The table team name. 
                
            supplementaryDatum
                The table team id.
                
            subsystem
                The subsystem (should be this one).
        RETURNS
            An event, that conforms to the IAuditEvent interface.
            
        SIDE EFFECTS
            None
        """
        assert subsystem == SUBSYSTEM, 'Subsystems do not match'
        
        # The process of picking the class used to create an event
        #   not a pretty one: use the code in a big if-statement.
        #   Not all data-items are passed to the constructors of
        #   the classes that represent the events: they do not need
        #   the code or subsystem, for example.
        if (code == JOIN):
            event = JoinEvent(context, event_id, date, 
              instanceUserInfo, siteInfo, groupInfo, instanceDatum)
        else:
            # If we get something odd, create a basic event with all
            #  the data we have. All call methods for audit-event
            #  factories will end in this call.
            event = BasicAuditEvent(context, event_id, UNKNOWN, date, 
              userInfo, instanceUserInfo, siteInfo, groupInfo, 
              instanceDatum, supplementaryDatum, SUBSYSTEM)
        assert event
        return event
    
    def getInterfaces(self):
        return implementedBy(BasicAuditEvent)

class JoinEvent(BasicAuditEvent):
    '''An audit-trail event representing a user being joined to a 
        group
    '''
    implements(IAuditEvent)

    def __init__(self, context, id, d, instanceUserInfo, siteInfo,
                  groupInfo, instanceDatum):
        """Create a join event
        """
        BasicAuditEvent.__init__(self, context, id,  JOIN, d, None,
          instanceUserInfo, siteInfo, groupInfo, instanceDatum, None, 
          SUBSYSTEM)
          
    def __str__(self):
        retval = u'%s (%s) joined %s (%s) on %s (%s). '\
          u'Email delivery is set to "%s".' % (
            self.instanceUserInfo.name, self.instanceUserInfo.id,
            self.groupInfo.name,        self.groupInfo.id,
            self.siteInfo.name,          self.siteInfo.id,
            self.instanceDatum)
        return retval
    
    @property
    def xhtml(self):
        cssClass = u'audit-event groupserver-group-member-%s' %\
          self.code
        retval = u'<span class="%s">Joined %s</span>'%\
          (cssClass, self.groupInfo.name)
        return retval

class JoinAuditor(object):
    """An Auditor for joining
    """
    def __init__(self, context):
        """Create an auditor.
        """
        self.context = context
        self.__instanceUserInfo = None
        self.__siteInfo = None
        self.__groupInfo = None
        self.__factory = None
        self.__queries = None
        
    @property
    def instanceUserInfo(self):
        if self.__instanceUserInfo == None:
            self.__instanceUserInfo =\
              createObject('groupserver.LoggedInUser', self.context)
        return self.__instanceUserInfo
        
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
            self.__factory = JoinAuditEventFactory()
        return self.__factory
        
    @property
    def queries(self):
        if self.__queries == None:
            self.__queries = AuditQuery(self.context.zsqlalchemy)
        return self.__queries
        
    def info(self, code, instanceDatum='', supplementaryDatum=''):
        """Log an info event to the audit trail.

        DESCRIPTION
            This method logs an event to the audit trail. It is
            named after the equivalent method in the standard Python
            logger, which it also writes to. The three arguments 
            (other than self) are combined to form the arguments to
            the factory, which creates the event that is then 
            recorded.
                
        ARGUMENTS
            "code"    The code that identifies the event that is 
                      logged. Sometimes this is enough.
                      
            "instanceDatum"
                      Data about the event. Each event class has its
                      own way to interpret this data.
                      
            "supplementaryDatum"
                      More data about an event.
        
        SIDE EFFECTS
            * Creates an ID for the new event,
            * Writes the instantiated event to the audit-table, and
            * Writes the event to the standard Python log.
        
        RETURNS
            None
        """
        d = datetime.now(UTC)
        eventId = event_id_from_data(self.instanceUserInfo, 
          self.instanceUserInfo, self.siteInfo, code, instanceDatum,
          '%s-%s' % (self.groupInfo.name, self.groupInfo.id))
          
        e = self.factory(self.context, eventId,  code, d,
          None, self.instanceUserInfo, self.siteInfo, 
          self.groupInfo, instanceDatum, None, SUBSYSTEM)
          
        self.queries.store(e)
        log.info(e)
        return e

