SELECT
    姓名,
    學號,
    大學
FROM
    dbo.使用者
WHERE
    卡號 = :card_id
    OR 學號 = :card_id