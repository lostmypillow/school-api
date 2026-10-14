SET ARITHABORT ON;
WITH FIRSTQUERY AS (
    SELECT TOP (1)
        [file_no],
        [course_name],
        [legacy_course_num]
    FROM
        [todays_seats]
),
SQ AS (
    SELECT
        STUFF((
            SELECT ',' + CAST([SEATS_RECORDS].SN AS NVARCHAR(MAX))
            FROM [seats_records]
            WHERE
                [SEATS_RECORDS].STUDENT_ID IS NULL
                AND [SEATS_RECORDS].FILE_NO = FQ.FILE_NO
            FOR XML PATH (''), TYPE
        ).value('.', 'NVARCHAR(MAX)'
        ), 1, 1, '') AS SEAT_NO,
        STUFF((
            SELECT ',' + CAST([SEATS_RECORDS].SEAT_NO AS NVARCHAR(MAX))
            FROM [seats_records]
            WHERE
                [SEATS_RECORDS].STUDENT_ID IS NULL
                AND [SEATS_RECORDS].FILE_NO = FQ.FILE_NO
            FOR XML PATH (''), TYPE
        ).value('.', 'NVARCHAR(MAX)'
        ), 1, 1, '') AS 座位
)
SELECT
    FQ.[file_no],
    FQ.[course_name],
    FQ.[legacy_course_num],
    SQ.SEAT_NO,
    SQ.座位
FROM FIRSTQUERY AS FQ
OUTER APPLY SQ
WHERE EXISTS (SELECT 1 FROM FIRSTQUERY);
