IF OBJECT_ID(N'semesters', N'U') IS NULL
BEGIN
CREATE TABLE semesters (
	id NVARCHAR(36) NOT NULL, 
	year NVARCHAR(10) NOT NULL, 
	sem NVARCHAR(10) NOT NULL, 
	link NVARCHAR(2048) NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL, 
	updated_at DATETIMEOFFSET NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_semesters_year_sem UNIQUE (year, sem)
)
END;

IF OBJECT_ID(N'departments', N'U') IS NULL
BEGIN
CREATE TABLE departments (
	id NVARCHAR(64) NOT NULL, 
	semester_id NVARCHAR(36) NOT NULL, 
	year NVARCHAR(10) NOT NULL, 
	sem NVARCHAR(10) NOT NULL, 
	code NVARCHAR(20) NOT NULL, 
	name NVARCHAR(255) NOT NULL, 
	link NVARCHAR(2048) NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL, 
	updated_at DATETIMEOFFSET NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_departments_year_sem_code UNIQUE (year, sem, code), 
	FOREIGN KEY(semester_id) REFERENCES semesters (id) ON DELETE CASCADE
)
END;

IF OBJECT_ID(N'department_years', N'U') IS NULL
BEGIN
CREATE TABLE department_years (
	id NVARCHAR(64) NOT NULL, 
	department_id NVARCHAR(64) NOT NULL, 
	year NVARCHAR(10) NOT NULL, 
	sem NVARCHAR(10) NOT NULL, 
	code NVARCHAR(20) NOT NULL, 
	name NVARCHAR(255) NOT NULL, 
	link NVARCHAR(2048) NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL, 
	updated_at DATETIMEOFFSET NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_department_years_year_sem_code UNIQUE (year, sem, code), 
	FOREIGN KEY(department_id) REFERENCES departments (id) ON DELETE CASCADE
)
END;

IF OBJECT_ID(N'courses', N'U') IS NULL
BEGIN
CREATE TABLE courses (
	id NVARCHAR(64) NOT NULL, 
	department_year_id NVARCHAR(64) NOT NULL, 
	year NVARCHAR(10) NOT NULL, 
	sem NVARCHAR(10) NOT NULL, 
	code NVARCHAR(50) NULL, 
	name NVARCHAR(255) NOT NULL, 
	link NVARCHAR(2048) NULL, 
	credits INTEGER NULL, 
	course_type NVARCHAR(20) NULL, 
	instructor NVARCHAR(255) NULL, 
	sun NVARCHAR(50) NULL, 
	mon NVARCHAR(50) NULL, 
	tue NVARCHAR(50) NULL, 
	wed NVARCHAR(50) NULL, 
	thu NVARCHAR(50) NULL, 
	fri NVARCHAR(50) NULL, 
	sat NVARCHAR(50) NULL, 
	classroom NVARCHAR(255) NULL, 
	students_enrolled INTEGER NULL, 
	students_dropped INTEGER NULL, 
	language NVARCHAR(50) NULL, 
	notes NTEXT NULL, 
	with_class NVARCHAR(255) NULL, 
	experiment NVARCHAR(255) NULL, 
	cross_discipline NVARCHAR(255) NULL, 
	created_at DATETIMEOFFSET NOT NULL, 
	updated_at DATETIMEOFFSET NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_courses_year_sem_code UNIQUE (id), 
	FOREIGN KEY(department_year_id) REFERENCES department_years (id) ON DELETE CASCADE
)
END;