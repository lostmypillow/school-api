WITH firstquery AS (
    SELECT
        course_name,
        legacy_course_num,
        top(1)
            AS file_no
    FROM
        todays_seats
)

SELECT
    fq.file_no,
    fq.course_name,
    fq.legacy_course_num,
    sq.seat_no,
    sq.seat
FROM firstquery AS fq
LEFT JOIN LATERAL (
    SELECT
        string_agg(seats_records.sn::text, ',') AS seat_no,
        string_agg(seat_no::text, ',') AS seat
    FROM seats_records
    WHERE
        seats_records.student_id IS NULL AND seats_records.file_no = fq.file_no
) AS sq ON TRUE
WHERE EXISTS (SELECT 1 FROM firstquery);
