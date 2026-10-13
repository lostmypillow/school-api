UPDATE
    seats_records
SET
    student_id = :student_id,
    created_at = GETDATE()
WHERE
    sn = :sn