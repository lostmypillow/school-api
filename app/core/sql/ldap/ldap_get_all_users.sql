SELECT
    student_id,
    name,
    pwd,
    main_department,
    employment_status
FROM
    employees
WHERE
    LENGTH(student_id) >= 6
    OR student_id = 'admin'
