INSERT INTO
    dbo.預約輔導 (日期, 學號, 老師編號, 上課時間)
VALUES
    (
        CONVERT(varchar, getdate(), 111),
        :student_id,
        :teacher_id,
        GETDATE()
    )