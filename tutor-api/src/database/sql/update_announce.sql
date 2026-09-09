UPDATE
    math_announcements
SET
    content = :content,
    updated_at = SYSDATETIME()
WHERE
    id = :id