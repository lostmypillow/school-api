SELECT
    id,
    student_id,
    dep_number,
    record_date,
    course_time,
    subject,
    rating,
    location
FROM
    student_survey_results
WHERE
    student_id = $1
    AND record_date = $2
    AND dep_number = $3;
