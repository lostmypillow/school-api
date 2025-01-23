SELECT
    教室,
    內容,
    left(CONVERT(varchar, 時間, 108), 5) 時間,
    
FROM
    課程列表
WHERE
    日期 = :current_date
    AND 時段 = :current_period
ORDER BY
    教室