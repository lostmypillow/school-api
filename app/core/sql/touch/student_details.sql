SELECT
    name,
    gender,
    TOP 1
        AS student_id
FROM
    students
WHERE
    card_id = ?
