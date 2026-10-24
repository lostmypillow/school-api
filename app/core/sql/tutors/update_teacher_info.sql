UPDATE
    employees
SET
    new_college = $1
WHERE
    card_id = $2
    OR id = $3;
