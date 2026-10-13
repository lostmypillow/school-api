SELECT
    TOP 1 *
FROM
    [seats_master]
WHERE
    getdate() BETWEEN [seats_master].starts_at
    AND [seats_master].ends_at


-- SELECT
--     TOP 1 *
-- FROM
--     [seats_master]
-- WHERE
--     '2020-09-16' BETWEEN [seats_master].starts_at
--     AND [seats_master].ends_at