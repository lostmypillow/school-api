 INSERT INTO trial_records
        ([employee_name], [category], [log_content], [record_date], [course_time], [computer_name], [student_id])
        OUTPUT Inserted.id AS id, Inserted.[record_date] AS date, Inserted.[course_time] AS time
        VALUES
        (:employee_name, :category, :log_content, GETDATE(), GETDATE(), :computer_name, :employee_id)