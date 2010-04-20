CREATE TABLE user_group_member_invitation (
    INVITATION_ID     TEXT                        PRIMARY KEY,
    USER_ID           TEXT                        NOT NULL,
    INVITING_USER_ID  TEXT                        NOT NULL,
    SITE_ID           TEXT                        NOT NULL,
    GROUP_ID          TEXT                        NOT NULL,
    INVITATION_DATE   TIMESTAMP WITH TIME ZONE    NOT NULL,
    RESPONSE_DATE     TIMESTAMP WITH TIME ZONE    DEFAULT NULL,
    ACCEPTED          BOOL                        DEFAULT FALSE
);
--=mpj17=-- There is no foreign key for user_id, yet

-- INVITATION_DATE is the date the user was invited to join the group
-- RESPONSE_DATE is the date the user responded to the invitation. If the
--    user has not responded to the invitation, it is NULL.
-- ACCEPTED is TRUE if the user accepted the invitation when he or she
--    responded; FALSE otherwise.

