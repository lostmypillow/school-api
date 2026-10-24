SELECT
    sn,
    file_no,
    seat_no,
    student_id,
    created_at
FROM
    seats_records
WHERE
    file_no = ?
    AND student_id = ?
    AND created_at::date = CURRENT_DATE;
