UPDATE
    math_announcements
SET
    content = ?,
    updated_at = SYSDATETIME()
WHERE
    id = ?;
