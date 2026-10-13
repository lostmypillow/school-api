UPDATE trial_records
        SET source = :source,
            student_id = :student_id,
            student_name = :student_name,
            middle_school_name = :middle_school_name,
            middle_school_class = :middle_school_class,
            high_school_name = :high_school_name,
            high_school_class = :high_school_class,
            registered_class = :registered_class,
            trial_date = :trial_date,
            telephone = :telephone,
            mobile = :mobile,
            notes = :notes,
            parent_name = :parent_name,
            manager = :manager,
            status = :status,
            current_grade = :current_grade, updated_at = GETDATE()
        OUTPUT Inserted.id, Inserted.created_at, Inserted.updated_at
        WHERE id = :id