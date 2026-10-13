 INSERT INTO trial_records
        (source, student_id, student_name, middle_school_name, middle_school_class,
         high_school_name, high_school_class, registered_class, trial_date,
         telephone, mobile, notes, parent_name, manager, status, current_grade,
         created_at, updated_at)
        OUTPUT Inserted.id, Inserted.created_at, Inserted.updated_at
        VALUES
        (:source, :student_id, :student_name, :middle_school_name, :middle_school_class,
         :high_school_name, :high_school_class, :registered_class, :trial_date,
         :telephone, :mobile, :notes, :parent_name, :manager, :status, :current_grade,
         GETDATE(), GETDATE())