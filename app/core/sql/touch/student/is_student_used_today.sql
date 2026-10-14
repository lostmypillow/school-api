SELECT
    [id],
    [student_id],
    [dep_number],
    [record_date],
    [course_time],
    [subject],
    [rating],
    [location]
FROM
    [student_survey_results]
WHERE
    [student_id] = ?
    AND [record_date] = ?
    AND [dep_number] = ?;
