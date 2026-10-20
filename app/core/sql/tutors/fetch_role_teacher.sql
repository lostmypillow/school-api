SELECT
    name,
    id,
    college,
    new_college
FROM
    employees
WHERE
    card_id = $1
    OR id = $2
