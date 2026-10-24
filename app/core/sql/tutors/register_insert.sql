INSERT INTO
dbo.tutor_appointments (date, student_id, teacher_id, start_time)
VALUES
(
    CONVERT(varchar, getdate(), 111),
    ?,
    ?,
    getdate()
);
