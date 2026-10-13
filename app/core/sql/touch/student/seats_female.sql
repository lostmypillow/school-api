SELECT
    [sn],
    [file_no],
    [seat_no]
FROM
    [seats_records]
WHERE
    file_no = :class_id
    AND [student_id] IS NULL
    AND CAST(RIGHT(seat_no, 2) AS INT) <= 15