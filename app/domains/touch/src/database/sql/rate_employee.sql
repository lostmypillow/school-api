INSERT INTO
    學生滿意度調查 (學號, 部門編號, 日期, 時間, 評分對象, 滿意度, 位置)
VALUES
    (
        :student_id,
        :department,
        CONVERT(char, getdate(), 112),
        CONVERT(char, getdate(), 120),
        :employee_id,
        :rating,
        ''
    );