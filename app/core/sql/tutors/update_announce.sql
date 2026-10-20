UPDATE
    math_announcements
SET
    content = $1,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = $2;
