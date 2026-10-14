MERGE INTO department_years AS target
USING
    (
        SELECT
            ? AS id,
            ? AS department_id,
            ? AS year,
            ? AS sem,
            ? AS code,
            ? AS name,
            ? AS link
    ) AS source
    ON target.id = source.id
WHEN MATCHED
    THEN
    UPDATE
        SET
            name = source.name,
            link = source.link,
            updated_at = SYSDATETIMEOFFSET()
WHEN NOT MATCHED
    THEN
    INSERT
        (id, department_id, year, sem, code, name, link, created_at, updated_at)
    VALUES (source.id, source.department_id, source.year, source.sem, source.code, source.name, source.link, SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET());
