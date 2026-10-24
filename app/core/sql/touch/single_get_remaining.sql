SET ARITHABORT ON;
WITH FIRSTQUERY AS (
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
    SQ.SEAT_NO,
    SQ.SEAT
FROM FIRSTQUERY AS FQ
OUTER APPLY ( -- noqa: ST05
    SELECT
        STUFF((
            SELECT ',' + CAST([seats_records].[sn] AS NVARCHAR(MAX))
            FROM [seats_records]
            WHERE
                [seats_records].[student_id] IS NULL
                AND [seats_records].[file_no] = FQ.[file_no]
            FOR XML PATH (''), TYPE
        ).value('.', 'NVARCHAR(MAX)'
        ), 1, 1, '') AS SEAT_NO,
        STUFF((
            SELECT ',' + CAST([seats_records].[seat_no] AS NVARCHAR(MAX))
            FROM [seats_records]
            WHERE
                [seats_records].[student_id] IS NULL
                AND [seats_records].[file_no] = FQ.[file_no]
            FOR XML PATH (''), TYPE
        ).value('.', 'NVARCHAR(MAX)'
        ), 1, 1, '') AS SEAT
) AS SQ
WHERE EXISTS (SELECT 1 FROM FIRSTQUERY);
