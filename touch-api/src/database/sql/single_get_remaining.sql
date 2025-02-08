-- WITH FirstQuery AS (
--     SELECT TOP (1) 
--         [主檔號],
--         [班級名稱],
--         [班別]
--     FROM 
--         [view_今日學生補位人數]
-- ),
-- SeatsQuery AS (
--     SELECT 
--         STRING_AGG(sn, ',') AS 座位號,
--         STRING_AGG(座位號, ',') AS 座位
--     FROM
--         [學生補位明細]
--     WHERE
--         學號 IS NULL
--         AND 主檔號 = (SELECT 主檔號 FROM FirstQuery)
-- )
-- SELECT 
--     FQ.[主檔號],
--     FQ.[班級名稱],
--     FQ.[班別],
--     SQ.座位號,
--     SQ.座位
-- FROM FirstQuery FQ, SeatsQuery SQ;
SET ARITHABORT ON;
WITH FirstQuery AS (
    SELECT TOP (1) 
        [主檔號],
        [班級名稱],
        [班別]
    FROM 
        [view_今日學生補位人數]
)
SELECT 
    FQ.[主檔號],
    FQ.[班級名稱],
    FQ.[班別],
    SQ.座位號,
    SQ.座位
FROM FirstQuery FQ
OUTER APPLY (
    SELECT 
        STUFF((SELECT ',' + CAST(sn AS NVARCHAR(MAX)) 
               FROM [學生補位明細]
               WHERE 學號 IS NULL AND 主檔號 = FQ.主檔號
               FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 座位號,
        STUFF((SELECT ',' + CAST(座位號 AS NVARCHAR(MAX)) 
               FROM [學生補位明細]
               WHERE 學號 IS NULL AND 主檔號 = FQ.主檔號
               FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS 座位
) SQ
WHERE EXISTS (SELECT 1 FROM FirstQuery);
