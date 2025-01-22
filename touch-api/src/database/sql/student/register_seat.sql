UPDATE
    學生補位明細
SET
    學號 = :student_id,
    登記時間 = GETDATE()
WHERE
    sn = :sn