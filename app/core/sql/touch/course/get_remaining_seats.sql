SELECT
    [sn],
    [seat_no]
FROM
    [seats_records]
WHERE
    file_no = 4
    AND student_id IS NULL