SELECT
    name,
    student_id
FROM
    students
WHERE
    card_id = $1
    OR student_id = $2;
