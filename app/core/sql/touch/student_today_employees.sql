SELECT
    u.student_id,
    u.name,
    u.main_department
FROM
    employees AS u
WHERE
    EXISTS (
        SELECT 1
        FROM
            employee_clock_records AS ecr
        WHERE
            ecr.student_id = u.student_id
            AND ecr.clock_in_date = $1
            AND ecr.main_department IN (2, 4, 8, 9, 11)
            AND ecr.job_type <> 1
    );
