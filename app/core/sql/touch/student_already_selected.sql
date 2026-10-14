SELECT
    [sn],
    [file_no],
    [seat_no],
    [student_id],
    [created_at]
FROM
    [seats_records]
WHERE
    [file_no] = ?
    AND [student_id] = ?
    AND CAST([created_at] AS DATE) = CAST(GETDATE() AS DATE);
