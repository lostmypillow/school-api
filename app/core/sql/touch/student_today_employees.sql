SELECT
    student_id,
    name,
    main_department
FROM
    users
WHERE
    student_id IN (
        SELECT
            student_id
        FROM
            employee_clock_records
        WHERE
            clock_in_date = :current_date)
            AND main_department IN (2,4,8,9,11)
            AND job_type <> 1