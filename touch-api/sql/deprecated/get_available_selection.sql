SELECT
    *
FROM
    學生滿意度調查
WHERE
    日期 >= :monday
    AND 學號 = :student_id
    AND 部門編號 IN (2, 4, 8, 11)