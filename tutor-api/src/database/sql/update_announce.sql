UPDATE
    math_announcements
SET
    content = :content,
    author = :author,
    updated_at = SYSDATETIME()
WHERE
    id = :id