WITH FirstQuery AS (
    SELECT TOP (1) 
        [主檔號],
        [班級名稱],
        [班別]
    FROM 
        [view_今日學生補位人數]
),
SeatsQuery AS (
    SELECT 
        STRING_AGG(sn, ',') AS 座位號,
        STRING_AGG(座位號, ',') AS 座位
    FROM
        [學生補位明細]
    WHERE
        學號 IS NULL
        AND 主檔號 = (SELECT 主檔號 FROM FirstQuery)
)
SELECT 
    FQ.[主檔號],
    FQ.[班級名稱],
    FQ.[班別],
    SQ.座位號,
    SQ.座位
FROM FirstQuery FQ, SeatsQuery SQ;