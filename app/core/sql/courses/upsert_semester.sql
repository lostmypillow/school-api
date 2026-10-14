MERGE INTO [semesters] AS [target]
USING (
    SELECT
        ? AS [id],
        ? AS [year],
        ? AS [sem],
        ? AS [link]
) AS [source]
    ON [target].[id] = [source].[id]
WHEN MATCHED
    THEN
    UPDATE
        SET
            [year] = [source].[year],
            [sem] = [source].[sem],
            [link] = [source].[link],
            [updated_at] = SYSDATETIMEOFFSET()
WHEN NOT MATCHED
    THEN
    INSERT ([id], [year], [sem], [link], [created_at], [updated_at])
    VALUES (
        [source].[id],
        [source].[year],
        [source].[sem],
        [source].[link],
        SYSDATETIMEOFFSET(),
        SYSDATETIMEOFFSET()
    );
