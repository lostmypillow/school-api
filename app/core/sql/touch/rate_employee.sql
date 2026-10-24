INSERT INTO
student_survey_results (
    student_id, dep_number, record_date, course_time, subject, rating, location
)
VALUES
(
    $1,
    $2,
    to_char(now(), 'YYYYMMDD'),
    to_char(now(), 'YYYY-MM-DD HH24:MI:SS'),
    $3,
    $4,
    ''
);
