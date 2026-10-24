SELECT [legacy_course_num].[legacy_course_num]
FROM
    [seats_master]
LEFT JOIN
    [legacy_course_num]
    ON [seats_master].[legacy_course_num] = [legacy_course_num].[id]
WHERE
    [seats_master].[legacy_course_num_2] IN (
        SELECT [accounts_owed].[legacy_course_num_2]
        FROM
            [accounts_owed]
        WHERE
            [accounts_owed].[student_id] = ?
            AND (
                [accounts_owed].[owes_money] <= 0
                OR [accounts_owed].[owed_amount] >= 3000
            )
    )
    AND GETDATE() BETWEEN [seats_master].[starts_at]
    AND [seats_master].[ends_at]
    AND [seats_master].[record_date] = CONVERT(CHAR(10), GETDATE(), 111)
