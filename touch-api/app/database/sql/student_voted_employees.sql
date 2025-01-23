SELECT
    評分對象
FROM
    學生滿意度調查
WHERE
    日期 > :monday
    AND 學號 = :student_id