WHILE EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE referenced_object_id = OBJECT_ID('dbo.department_years')
)
    BEGIN
        DECLARE @sql NVARCHAR(MAX);
        SELECT TOP 1
            @sql
            = 'ALTER TABLE '
            + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
            + '.'
            + QUOTENAME(OBJECT_NAME(parent_object_id))
            + ' DROP CONSTRAINT '
            + QUOTENAME(name)
        FROM sys.foreign_keys
        WHERE referenced_object_id = OBJECT_ID('dbo.department_years');
        EXEC sp_executesql @sql;
    END;

IF OBJECT_ID('dbo.department_years', 'U') IS NOT NULL
    BEGIN
        DROP TABLE dbo.department_years;
    END;
