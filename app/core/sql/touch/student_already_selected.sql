SELECT
    *
FROM
    seats_records
WHERE
    file_no = :course_id
    AND student_id = :student_id
    AND CAST(created_at AS DATE) = CAST(GETDATE() AS DATE);