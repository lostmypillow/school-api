-- Check if the table exists, and if not, create it
IF
    NOT EXISTS (
        SELECT *
        FROM
            information_schema.tables
        WHERE
            table_name = 'devices'
    )
    BEGIN
        CREATE TABLE devices (
            [id] INT PRIMARY KEY,
            [teacher_id] VARCHAR(20)
        );

    END;

-- Insert ascending numbers up to 6, ensuring that the numbers fill the gaps if needed
DECLARE @i INT = 1;

WHILE @i <= 6
    BEGIN
        IF
            NOT EXISTS (
                SELECT 1
                FROM
                    devices
                WHERE
                    [id] = @i
            )
            BEGIN
                INSERT INTO
                devices ([id], [teacher_id])
                VALUES
                (@i, NULL);

                -- Use @i to insert the ascending number
            END
        SET
            @i = @i + 1;

    END;

-- Bootstrap test student (ID: 111111)
IF
    NOT EXISTS (
        SELECT 1 FROM dbo.students
        WHERE student_id = '111111'
    )
    BEGIN
        INSERT INTO dbo.students (student_id, name, card_id)
        VALUES ('111111', N'測試學生', '111111');
    END;

-- Bootstrap test teacher (ID: 222222, department='9' required for teacher role)
IF NOT EXISTS (
    SELECT 1 FROM dbo.users
    WHERE id = '222222'
) BEGIN
    INSERT INTO dbo.users (id, name, card_id, college, new_college, department)
    VALUES ('222222', N'測試老師', '222222', N'理學院', N'新理學院', '9');
END;
