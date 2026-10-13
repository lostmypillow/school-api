SET ARITHABORT ON;
WITH FirstQuery AS (
    SELECT TOP (1) 
        [file_no],
        [course_name],
        [legacy_course_num]
    FROM 
        [todays_seats]
)
SELECT 
    FQ.[file_no],
    FQ.[course_name],
    FQ.[legacy_course_num],
    SQ.seat_no,
    SQ.座位
FROM FirstQuery FQ
OUTER APPLY (
    SELECT 
        STUFF((SELECT ',' + CAST(sn AS NVARCHAR(MAX)) 
               FROM [seats_records]
               WHERE student_id IS NULL AND file_no = FQ.file_no
               FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS seat_no,
        STUFF((SELECT ',' + CAST(seat_no AS NVARCHAR(MAX))
               FROM [seats_records]
               WHERE student_id IS NULL AND file_no = FQ.file_no
               FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 座位
) SQ
WHERE EXISTS (SELECT 1 FROM FirstQuery);
