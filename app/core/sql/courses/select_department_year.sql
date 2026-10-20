SELECT
    id,
    department_id,
    year,
    sem,
    code,
    name,
    link,
    created_at,
    updated_at
FROM
    department_years
WHERE
    department_id = $1
