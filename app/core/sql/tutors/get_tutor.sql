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
WHERE
    id = $1;
