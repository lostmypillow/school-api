-- Check if the table exists, and if not, create it
IF NOT EXISTS (
    SELECT
        *
    FROM
        information_schema.tables
    WHERE
        table_name = '設備資料'
) BEGIN CREATE TABLE 設備資料 (
    [設備號碼] INT PRIMARY KEY,
    [老師編號] VARCHAR(7)
);

END;

-- Insert ascending numbers up to 6, ensuring that the numbers fill the gaps if needed
DECLARE @i INT = 1;

WHILE @i <= 6 BEGIN IF NOT EXISTS (
    SELECT
        1
    FROM
        設備資料
    WHERE
        [設備號碼] = @i
) BEGIN
INSERT INTO
    設備資料 ([設備號碼], [老師編號])
VALUES
    (@i, NULL);

-- Use @i to insert the ascending number
END
SET
    @i = @i + 1;

END;