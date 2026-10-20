SELECT subject
FROM
    student_survey_results
WHERE
    course_time > $1
    AND student_id = $2
