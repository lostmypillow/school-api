SELECT
    subject
FROM
    student_survey_results
WHERE
    course_time > :monday
    AND student_id = :student_id