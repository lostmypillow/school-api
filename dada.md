
---

### 1. Missing Tables and Required Columns

| Table Name (as queried)      | Type       | Columns & Data Types                                                                                                                                                                                                          | Notes / Usage                                                                                                                                                          |
|:-----------------------------|:-----------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **`seats_records`**          | Table      | • `sn` (INT, PK/Identity)<br>• `file_no` (INT, FK)<br>• `seat_no` (VARCHAR(20))<br>• `student_id` (VARCHAR(20), NULL)<br>• `created_at` (DATETIME, NULL)                                                                      | Used by `register_seat`, `single_get_remaining`, `student_already_selected`, `seats_male/female`. Seat number trailing 2 digits `<= 15` for females, `> 15` for males. |
| **`seats_master`**           | Table      | • `file_no` (INT, PK)<br>• `legacy_course_num` (INT / VARCHAR(20))<br>• `legacy_course_num_2` (VARCHAR(20))<br>• `starts_at` (DATETIME)<br>• `ends_at` (DATETIME)<br>• `record_date` (CHAR(10), `YYYY/MM/DD`)                 | Used by `student_match_course` and `seats/available`. Checks if current time is within `starts_at` and `ends_at`.                                                      |
| **`legacy_course_num`**      | Table      | • `id` (INT / VARCHAR(20), PK)<br>• `legacy_course_num` (NVARCHAR(50))                                                                                                                                                        | Joined with `seats_master` in `student_match_course` to match class division name (e.g. `A班`).                                                                        |
| **`accounts_owed`**          | Table      | • `student_id` (VARCHAR(20))<br>• `legacy_course_num_2` (VARCHAR(20))<br>• `owes_money` (DECIMAL / INT)<br>• `owed_amount` (DECIMAL / INT)                                                                                    | Used in `student_match_course` to verify qualification (`owes_money <= 0 OR owed_amount >= 3000`).                                                                     |
| **`todays_seats`**           | View/Table | • `file_no` (INT)<br>• `course_name` (NVARCHAR(100))<br>• `legacy_course_num` (NVARCHAR(50))                                                                                                                                  | Used in `single_get_remaining` and `seats/remaining` to get current active class for seat allocation.                                                                  |
| **`legacy_course_list`**     | Table      | • `classroom` (INT)<br>• `contents` (NVARCHAR(255))<br>• `course_time` (TIME / DATETIME)<br>• `record_date` (VARCHAR(10), `YYYY/MM/DD`)<br>• `time_slot` (INT: 1, 2, or 3)                                                    | Used by `classes_today` in kiosk display. `classroom` is 1-based index (1–5).                                                                                          |
| **`student_survey_results`** | Table      | • `student_id` (VARCHAR(20))<br>• `dep_number` (INT)<br>• `record_date` (CHAR(8), `YYYYMMDD`)<br>• `course_time` (VARCHAR(20) / DATETIME)<br>• `subject` (VARCHAR(20))<br>• `rating` (INT, 1–5)<br>• `location` (VARCHAR(50)) | Target of `rate_employee`. Also queried in `student_voted_employees` to filter out already-rated staff.                                                                |
| **`employee_clock_records`** | Table      | • `student_id` (VARCHAR(20))<br>• `clock_in_date` (VARCHAR(10), `YYYY-MM-DD`)                                                                                                                                                 | Used in `student_today_employees` to find who is on duty today.                                                                                                        |
| **`employee_photos`**        | Table      | • `student_id` (VARCHAR(20))<br>• `photo_bytes` (VARBINARY(MAX))                                                                                                                                                              | Queried by `picture_employee`.                                                                                                                                         |
| **`student_photos`**         | Table      | • `student_id` (VARCHAR(20))<br>• `photo_bytes` (VARBINARY(MAX))                                                                                                                                                              | Queried by `picture_student`.                                                                                                                                          |

*(Note: Touch SQL directly references Chinese table names `students` and `users`. If these are not created as views/synonyms of `students` and `users`, they must be created as standalone tables with the columns shown below).*

---

### 2. Existing Models to Update in `app/core/models`

In [app/core/models/tutors/student.py](file:///Users/jlin/PycharmProjects/school-api/app/core/models/tutors/student.py) (`students` / `students`):
- **Columns to add:**
  - `gender` / `gender`: `Unicode(10)` (Values: `"male"` or `"female"`, required by [student_details.sql](file:///Users/jlin/PycharmProjects/school-api/app/core/sql/touch/student_details.sql) and validated by `AuthResponse`).

In [app/core/models/tutors/user.py](file:///Users/jlin/PycharmProjects/school-api/app/core/models/tutors/user.py) (`users` / `users`):
- **Columns to add:**
  - `main_department` / `main_department`: `Integer` (Administrative department code `2`, `4`, `8`, `9`, or `11` as mapped in `deps.py`, queried by [get_dep_number.sql](file:///Users/jlin/PycharmProjects/school-api/app/core/sql/touch/get_dep_number.sql) and [student_today_employees.sql](file:///Users/jlin/PycharmProjects/school-api/app/core/sql/touch/student_today_employees.sql)).
  - `job_type` / `job_type`: `Integer` (Must be `<> 1` for eligible survey targets, queried by [student_today_employees.sql](file:///Users/jlin/PycharmProjects/school-api/app/core/sql/touch/student_today_employees.sql)).

---

### 3. Initial Mock Values for Demo Run

For a demo student (`student_id = "111111"`) and employee (`employee_id = "222222"`):

1. **`students` (or `students`):**
   - `student_id`: `'111111'`
   - `name`: `N'測試學生'`
   - `gender`: `N'male'` (or `N'female'`)
   - `card_id`: `'111111'`

2. **`users` (or `users`):**
   - `student_id`: `'222222'`
   - `name`: `N'測試老師'`
   - `main_department`: `2` (maps to `"教務處"` in `deps.py`)
   - `job_type`: `2` (`<> 1`)

3. **`employee_clock_records`:**
   - `student_id`: `'222222'`
   - `clock_in_date`: Today's date `CONVERT(char(10), GETDATE(), 23)` (e.g., `'2026-10-13'`)

4. **`todays_seats`:**
   - `file_no`: `1`
   - `course_name`: `N'英文衝刺班'`
   - `legacy_course_num`: `N'A班'`

5. **`legacy_course_num`:**
   - `id`: `1`
   - `legacy_course_num`: `N'A班'`

6. **`seats_master`:**
   - `file_no`: `1`
   - `legacy_course_num`: `1`
   - `legacy_course_num_2`: `'ENG101'`
   - `starts_at`: `DATEADD(hour, -2, GETDATE())`
   - `ends_at`: `DATEADD(hour, 4, GETDATE())`
   - `record_date`: `CONVERT(char(10), GETDATE(), 111)` (`'YYYY/MM/DD'`)

7. **`accounts_owed`:**
   - `student_id`: `'111111'`
   - `legacy_course_num_2`: `'ENG101'`
   - `owes_money`: `0`
   - `owed_amount`: `3000`

8. **`seats_records`:**
   - Row 1 (Female seat `<= 15`): `sn = 1, file_no = 1, seat_no = 'A01', student_id = NULL, created_at = NULL`
   - Row 2 (Male seat `> 15`): `sn = 2, file_no = 1, seat_no = 'A17', student_id = NULL, created_at = NULL`

9. **`legacy_course_list`:**
   - `classroom`: `1`
   - `contents`: `N'高階微積分'`
   - `course_time`: `'14:00:00'`
   - `record_date`: `CONVERT(char(10), GETDATE(), 111)` (`'YYYY/MM/DD'`)
   - `time_slot`: `2` (or current period based on system hour: 1 for `<=10`, 2 for `11–16`, 3 for `>16`)