UPDATE
    dbo.使用者
SET
    新大學 = :college
WHERE
    卡號 = :card_id
    OR 學號 = :card_id