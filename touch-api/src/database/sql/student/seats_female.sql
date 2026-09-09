SELECT
    [sn],
    [主檔號],
    [座位號]
FROM
    [學生補位明細]
WHERE
    主檔號 = :class_id
    AND [學號] IS NULL
    AND CAST(RIGHT(座位號, 2) AS INT) <= 15