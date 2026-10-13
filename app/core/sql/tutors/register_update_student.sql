UPDATE
    dbo.tutor_appointments
SET
    end_time = GETDATE()
WHERE
    id = ?;
