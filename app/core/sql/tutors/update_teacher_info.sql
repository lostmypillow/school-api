UPDATE
    dbo.employees
SET
    new_college = ?
WHERE
    card_id = ?
    OR id = ?;
