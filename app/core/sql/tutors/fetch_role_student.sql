SELECT
    name,
    student_id
FROM
    dbo.students
WHERE
    card_id = ?
    OR student_id = ?;
