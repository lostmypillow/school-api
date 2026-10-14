UPDATE trial_records
SET
    source = ?,
    student_id = ?,
    student_name = ?,
    middle_school_name = ?,
    middle_school_class = ?,
    high_school_name = ?,
    high_school_class = ?,
    registered_class = ?,
    trial_date = ?,
    telephone = ?,
    mobile = ?,
    notes = ?,
    parent_name = ?,
    manager = ?,
    status = ?,
    current_grade = ?, updated_at = GETDATE()
OUTPUT INSERTED.id, INSERTED.created_at, INSERTED.updated_at
WHERE id = ?
