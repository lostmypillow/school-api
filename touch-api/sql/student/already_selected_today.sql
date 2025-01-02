SELECT
    *
FROM
    學生補位明細
WHERE
    主檔號 = :class_id
    AND 學號 = :student_id