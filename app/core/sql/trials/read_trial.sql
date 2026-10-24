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
    updated_at
FROM trial_records
WHERE id = $1
