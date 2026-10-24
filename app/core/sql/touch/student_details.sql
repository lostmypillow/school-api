SELECT TOP 1
    student_id,
    name,
    gender
FROM
    students
WHERE
    card_id = ?
