select
    [id],
    [course_id],
    [instructor_name],
    [email],
    [instructor_schedule],
    [abstract],
    [syllabus],
    [grading_policy],
    [materials],
    [consultation],
    [ai],
    [notes],
    [sdg],
    [last_updated]
from course_syllabi
where course_id = ?
