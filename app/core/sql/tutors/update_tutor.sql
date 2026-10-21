UPDATE
    employees
SET
    name = COALESCE($2, name),
    card_id = COALESCE($3, card_id),
    college = COALESCE($4, college),
    new_college = COALESCE($5, new_college),
    department = COALESCE($6, department),
    email = COALESCE($7, email)
WHERE
    id = $1;
