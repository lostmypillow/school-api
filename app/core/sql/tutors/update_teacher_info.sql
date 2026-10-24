UPDATE
    dbo.users
SET
    new_college = ?
WHERE
    card_id = ?
    OR id = ?;
