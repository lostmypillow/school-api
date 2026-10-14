INSERT INTO trial_records
(
    [employee_name],
    [category],
    [log_content],
    [record_date],
    [course_time],
    [computer_name],
    [student_id]
)
OUTPUT
    INSERTED.id AS id,
    INSERTED.[record_date] AS date,
    INSERTED.[course_time] AS time
VALUES
(?, ?, ?, GETDATE(), GETDATE(), ?, ?)
