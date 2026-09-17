SELECT
    姓名,
    學號
FROM
    dbo.學生資料
WHERE
    卡號 = :card_id
    OR 學號 = :card_id