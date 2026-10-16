SELECT
    [student_id] AS uid,
    [name] AS cn,
    新密碼 AS pwd,
    [main_department] AS main_grp,
    部門 AS other_grp,
    狀態 AS employment_status
FROM
    [employees]
WHERE
    LEN(student_id) >= 6
    OR student_id = 'admin'
