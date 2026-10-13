SELECT
    classroom,
    contents,
    left(CONVERT(varchar, course_time, 108), 5) course_time,
    
FROM
    legacy_course_list
WHERE
    record_date = :current_date
    AND time_slot = :current_period
ORDER BY
    classroom