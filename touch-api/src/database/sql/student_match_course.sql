SELECT 
    班別.班別
FROM 
    [學生補位主檔]
LEFT JOIN 
    班別 ON [學生補位主檔].班別代碼 = 班別.代碼
WHERE 
    [學生補位主檔].班級代碼 IN (
        SELECT 
            班級代碼
        FROM 
            學生欠費
        WHERE 
            學號 = :student_id
            AND (欠費 <= 0 OR 金額 >= 3000)
    )
    AND GETDATE() BETWEEN [學生補位主檔].開始時間 AND [學生補位主檔].結束時間
    AND [學生補位主檔].日期 = CONVERT(char(10), GETDATE(), 111)
