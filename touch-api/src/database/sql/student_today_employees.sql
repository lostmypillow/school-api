SELECT
    學號,
    姓名,
    主要部門
FROM
    使用者
WHERE
    學號 IN (
        SELECT
            學號
        FROM
            員工刷卡班表
        WHERE
            上班日期 = :current_date)
            AND 主要部門 IN (2,4,8,9,11)
            AND 職務別 <> 1