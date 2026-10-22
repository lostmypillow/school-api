WITH res AS (
    SELECT
        id,
        source,
        student_id,
        student_name,
        middle_school_name,
        middle_school_class,
        high_school_name,
        high_school_class,
        registered_class,
        trial_date,
        telephone,
        mobile,
        notes,
        parent_name,
        manager,
        status,
        current_grade,
        created_at,
        updated_at,
        ROW_NUMBER() OVER (ORDER BY created_at DESC) AS row_num,
        COUNT(*) OVER () AS total_count
    FROM trial_records
)

SELECT
    id,
    source,
    student_id,
    student_name,
    middle_school_name,
    middle_school_class,
    high_school_name,
    high_school_class,
    registered_class,
    trial_date,
    telephone,
    mobile,
    notes,
    parent_name,
    manager,
    status,
    current_grade,
    created_at,
    updated_at,
    total_count
FROM res
WHERE row_num > $1 AND row_num <= ($2 + $2)
ORDER BY created_at DESC;
