# coding=utf-8
import time, md5
from Products.XWFCore.XWFUtils import convert_int2b62

def invite_id(siteId, groupId, userId, adminId):
    istr = time.asctime() + siteId + groupId + userId + adminId
    inum = long(md5.new(istr).hexdigest(), 16)
    retval = str(convert_int2b62(inum))
    assert retval
    assert type(retval) == str
    return retval

