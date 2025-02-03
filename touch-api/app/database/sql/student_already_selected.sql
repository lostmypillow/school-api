SELECT
    *
FROM
    學生補位明細
WHERE
    主檔號 = :course_id
    AND 學號 = :student_id
    AND CAST(登記時間 AS DATE) = CAST(GETDATE() AS DATE);