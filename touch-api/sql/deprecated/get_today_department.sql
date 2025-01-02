SELECT
    department.主要部門,
    [員工部門].部門
FROM
    (
        SELECT
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
                    上班日期 = '2020-09-16'
            )
            AND 主要部門 IN (2, 4, 8, 11)
            AND 職務別 <> 1
    ) AS department
    LEFT JOIN [員工部門] ON department.主要部門 = [員工部門].自動編號