INSERT INTO
tutor_appointments (date, student_id, teacher_id, start_time)
VALUES
(
    CONVERT(varchar, NOW(), 111),
    $1,
    $2,
    NOW()
);
