SELECT
    TOP 1 學號,
    姓名,
    性別
FROM
    學生資料
WHERE
    學號 = :card_id
    OR 卡號 = :card_id