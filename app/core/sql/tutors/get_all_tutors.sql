SELECT
    id,
    name,
    card_id,
    college,
    new_college,
    department,
    email
FROM
    employees
ORDER BY
    id ASC
LIMIT $1 OFFSET $2;
