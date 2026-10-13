SELECT
    TOP 1 student_id,
    name,
    gender
FROM
    students
WHERE
    student_id = :card_id
    OR card_id = :card_id