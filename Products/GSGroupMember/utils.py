# coding=utf-8
import time, md5
from Products.XWFCore.XWFUtils import convert_int2b62, getOption

def invite_id(siteId, groupId, userId, adminId):
    istr = time.asctime() + siteId + groupId + userId + adminId
    inum = long(md5.new(istr).hexdigest(), 16)
    retval = str(convert_int2b62(inum))
    assert retval
    assert type(retval) == str
    return retval

def inform_ptn_coach_of_join(ptnCoachInfo, newUserInfo, groupInfo):
    assert ptnCoachInfo
    assert newUserInfo
    assert groupInfo
    siteInfo = groupInfo.siteInfo
    n_dict = {
        'groupId'      : groupInfo.id,
        'groupName'    : groupInfo.name,
        'groupUrl'     : groupInfo.url,
        'siteName'     : siteInfo.name,
        'canonical'    : siteInfo.url,
        'supportEmail' : getOption(groupInfo.groupObj, 'supportEmail'),
        'memberId'     : newUserInfo.id,
        'memberName'   : newUserInfo.name,
        'memberUrl'    : newUserInfo.url,
        'joining_user' : newUserInfo.user,
        'joining_group': groupInfo.groupObj,
    }
    if not ptnCoachInfo.anonymous:
        ptnCoachInfo.user.send_notification('join_group_admin', 
                                            groupInfo.id, n_dict)

