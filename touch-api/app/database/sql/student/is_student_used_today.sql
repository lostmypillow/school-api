SELECT
    *
FROM
    學生滿意度調查
WHERE
    學號 = :student_id
    AND 日期 = :current_date
    (:department_id IS NULL OR 部門編號 = :department_id);