from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class

xwfutils_security = ModuleSecurityInfo('Products.GSGroupMember.groupmembership')
xwfutils_security.declarePublic('get_group_users')
xwfutils_security.declarePublic('get_unverified_group_users')

