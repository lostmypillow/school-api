-- SELECT
--     TOP 1 *
-- FROM
--     [學生補位主檔]
-- WHERE
--     getdate() BETWEEN [學生補位主檔].開始時間
--     AND [學生補位主檔].結束時間


SELECT
    TOP 1 *
FROM
    [學生補位主檔]
WHERE
    '2020-09-16' BETWEEN [學生補位主檔].開始時間
    AND [學生補位主檔].結束時間