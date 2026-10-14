INSERT INTO
student_survey_results (
    student_id, dep_number, record_date, course_time, subject, rating, location
)
VALUES
(
    ?,
    ?,
    CONVERT(char, getdate(), 112),
    CONVERT(char, getdate(), 120),
    ?,
    ?,
    ''
);
