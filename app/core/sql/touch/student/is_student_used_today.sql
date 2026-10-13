SELECT
    *
FROM
    student_survey_results
WHERE
    student_id = :student_id
    AND record_date = :current_date
    (:department_id IS NULL OR dep_number = :department_id);