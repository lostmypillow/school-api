SELECT
    name,
    id,
    college,
    new_college
FROM
    dbo.employees
WHERE
    card_id = ?
    OR id = ?
