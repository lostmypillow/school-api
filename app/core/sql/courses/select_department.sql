SELECT
    [id],
    [semester_id],
    [year],
    [sem],
    [code],
    [name],
    [link],
    [created_at],
    [updated_at]
FROM
    [departments]
WHERE
    [semester_id] = ?