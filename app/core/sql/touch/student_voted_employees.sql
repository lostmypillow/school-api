SELECT subject
FROM
    student_survey_results
WHERE
    course_time > ?
    AND student_id = ?
