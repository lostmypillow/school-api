SELECT
    name,
    id,
    college,
    new_college
FROM
    dbo.users
WHERE
    card_id = ?
    OR id = ?
    AND department = '9';
