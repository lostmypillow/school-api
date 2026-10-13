SELECT
    id
FROM
    dbo.tutor_appointments
WHERE
    date = CONVERT(varchar, getdate(), 111)
    AND student_id = ?
    AND teacher_id = ?
    AND end_time IS NULL;
