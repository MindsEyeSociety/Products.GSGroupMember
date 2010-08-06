# coding=utf-8
from Products.XWFCore.XWFUtils import getOption

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

