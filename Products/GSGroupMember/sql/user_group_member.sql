create table user_group_membership (
    SITE_ID     TEXT                      NOT NULL,
    GROUP_ID    TEXT                      NOT NULL,
    USER_ID     TEXT                      NOT NULL,
    JOIN_DATE   TIMESTAMP WITH TIME ZONE  NOT NULL,
    LEAVE_DATE  TIMESTAMP WITH TIME ZONE  DEFAULT NULL
);
CREATE UNIQUE INDEX USER_GROUP_MEMBERSHIP_PKEY 
ON user_group_membership 
USING BTREE(SITE_ID, GROUP_ID, USER_ID, JOIN_DATE);
-- If the leave date is NULL, then the user is still a member of the group.
-- All users who are members of groups in the site are members of the site,
--    but it is possible (but rare) to have people who are members of a 
--    site but are not members of a group.

