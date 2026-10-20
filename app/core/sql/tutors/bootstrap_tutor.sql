CREATE TABLE IF NOT EXISTS devices (
    id INT PRIMARY KEY,
    teacher_id VARCHAR(20)
);

INSERT INTO devices (id, teacher_id)
SELECT
    s AS id,
    NULL AS teacher_id
FROM generate_series(1, 6) AS s
ON CONFLICT (id) DO NOTHING;

INSERT INTO students (student_id, name, card_id)
VALUES ('111111', '測試學生', '111111') ON CONFLICT (student_id) DO NOTHING;
