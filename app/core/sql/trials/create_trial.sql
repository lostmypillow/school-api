INSERT INTO trial_records
(
    source, student_id, student_name, middle_school_name, middle_school_class,
    high_school_name, high_school_class, registered_class, trial_date,
    telephone, mobile, notes, parent_name, manager, status, current_grade,
    created_at, updated_at
)
VALUES
(
    $1, $2, $3, $4, $5,
    $6, $7, $8, $9,
    $10, $11, $12, $13, $14, $15, $16,
    NOW(), NOW()
)
RETURNING id, created_at, updated_at
