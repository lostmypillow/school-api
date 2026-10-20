INSERT INTO trial_records
(
    employee_name,
    category,
    log_content,
    record_date,
    course_time,
    computer_name,
    student_id
)

VALUES
($1, $2, $3, NOW(), NOW(), $4, $5)
RETURNING id, record_date, course_time
