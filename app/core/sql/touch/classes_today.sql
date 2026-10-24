SELECT
    classroom,
    contents,
    to_char(course_time, 'HH24:MI') AS course_time
FROM
    legacy_course_list
WHERE
    record_date = $1
    AND time_slot = $2
ORDER BY
    classroom
