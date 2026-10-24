SELECT id
FROM
    tutor_appointments
WHERE
    date = to_char(now(), 'YYYY/MM/DD')
    AND student_id = $1
    AND teacher_id = $2
    AND end_time IS NULL;
