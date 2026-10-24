UPDATE
    seats_records
SET
    student_id = ?,
    created_at = NOW()
WHERE
    sn = $1
