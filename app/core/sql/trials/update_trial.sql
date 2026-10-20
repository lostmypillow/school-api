UPDATE trial_records
SET
    source = $1,
    student_id = $2,
    student_name = $3,
    middle_school_name = $4,
    middle_school_class = $5,
    high_school_name = $6,
    high_school_class = $7,
    registered_class = $8,
    trial_date = $9,
    telephone = $10,
    mobile = $11,
    notes = $12,
    parent_name = $13,
    manager = $14,
    status = $15,
    current_grade = $16, updated_at = NOW()
WHERE id = $17
RETURNING id, created_at, updated_at;
