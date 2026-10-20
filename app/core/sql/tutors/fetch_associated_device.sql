SELECT id
FROM
    devices
WHERE
    teacher_id = $1;
