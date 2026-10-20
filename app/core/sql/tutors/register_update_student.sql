UPDATE
    tutor_appointments
SET
    end_time = NOW()
WHERE
    id = $1;
