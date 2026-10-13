MERGE INTO courses AS target
USING (SELECT 
    ? AS id, ? AS department_year_id, ? AS year, ? AS sem, ? AS code, ? AS name, ? AS link, 
    ? AS credits, ? AS course_type, ? AS instructor, ? AS sun, ? AS mon, ? AS tue, ? AS wed, 
    ? AS thu, ? AS fri, ? AS sat, ? AS classroom, ? AS students_enrolled, ? AS students_dropped, 
    ? AS language, ? AS notes, ? AS with_class, ? AS experiment, ? AS cross_discipline
) AS source
ON target.id = source.id
WHEN MATCHED THEN
    UPDATE SET 
        name = source.name, link = source.link, credits = source.credits, course_type = source.course_type,
        instructor = source.instructor, sun = source.sun, mon = source.mon, tue = source.tue, wed = source.wed,
        thu = source.thu, fri = source.fri, sat = source.sat, classroom = source.classroom,
        students_enrolled = source.students_enrolled, students_dropped = source.students_dropped,
        language = source.language, notes = source.notes, with_class = source.with_class,
        experiment = source.experiment, cross_discipline = source.cross_discipline,
        updated_at = SYSDATETIMEOFFSET()
WHEN NOT MATCHED THEN
    INSERT (
        id, department_year_id, year, sem, code, name, link, credits, course_type, instructor,
        sun, mon, tue, wed, thu, fri, sat, classroom, students_enrolled, students_dropped,
        language, notes, with_class, experiment, cross_discipline, created_at, updated_at
    )
    VALUES (
        source.id, source.department_year_id, source.year, source.sem, source.code, source.name, source.link,
        source.credits, source.course_type, source.instructor, source.sun, source.mon, source.tue, source.wed,
        source.thu, source.fri, source.sat, source.classroom, source.students_enrolled, source.students_dropped,
        source.language, source.notes, source.with_class, source.experiment, source.cross_discipline,
        SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET()
    );
