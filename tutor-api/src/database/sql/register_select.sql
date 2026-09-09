SELECT
    自動編號
FROM
    dbo.預約輔導
WHERE
    日期 = CONVERT(varchar, getdate(), 111)
    AND 學號 = :student_id
    AND 老師編號 = :teacher_id
    AND 下課時間 IS NULL