SELECT 
    legacy_course_num.legacy_course_num
FROM 
    [seats_master]
LEFT JOIN 
    legacy_course_num ON [seats_master].legacy_course_num = legacy_course_num.id
WHERE 
    [seats_master].legacy_course_num_2 IN (
        SELECT 
            legacy_course_num_2
        FROM 
            accounts_owed
        WHERE 
            student_id = :student_id
            AND (owes_money <= 0 OR owed_amount >= 3000)
    )
    AND GETDATE() BETWEEN [seats_master].starts_at AND [seats_master].ends_at
    AND [seats_master].record_date = CONVERT(char(10), GETDATE(), 111)
    -- AND CAST('2024-08-22' AS datetime) BETWEEN [seats_master].starts_at AND [seats_master].ends_at
    -- AND [seats_master].record_date = CONVERT(char(10), CAST('2024-08-22' AS datetime), 111)
