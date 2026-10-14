SELECT
    [classroom],
    [contents],
    LEFT(CONVERT(VARCHAR, [course_time], 108), 5) AS [course_time]
FROM
    [legacy_course_list]
WHERE
    [record_date] = ?
    AND [time_slot] = ?
ORDER BY
    [classroom]
