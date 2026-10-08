-- Schema for SQLite (aiosqlite)

CREATE TABLE IF NOT EXISTS semesters (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    year VARCHAR(10) NOT NULL,
    sem VARCHAR(10) NOT NULL,
    link VARCHAR(2048) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_semesters_year_sem UNIQUE (year, sem)
);

CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    semester_id VARCHAR(36) NOT NULL,
    year VARCHAR(10) NOT NULL,
    sem VARCHAR(10) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(2048) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_departments_year_sem_code UNIQUE (year, sem, code),
    FOREIGN KEY (semester_id) REFERENCES semesters (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS department_years (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    department_id VARCHAR(64) NOT NULL,
    year VARCHAR(10) NOT NULL,
    sem VARCHAR(10) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(2048) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_department_years_year_sem_code UNIQUE (year, sem, code),
    FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS courses (
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    department_year_id VARCHAR(64) NOT NULL,
    year VARCHAR(10) NOT NULL,
    sem VARCHAR(10) NOT NULL,
    code VARCHAR(50) NULL,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(2048) NULL,
    credits INTEGER NULL,
    course_type VARCHAR(20) NULL,
    instructor VARCHAR(255) NULL,
    sun VARCHAR(50) NULL,
    mon VARCHAR(50) NULL,
    tue VARCHAR(50) NULL,
    wed VARCHAR(50) NULL,
    thu VARCHAR(50) NULL,
    fri VARCHAR(50) NULL,
    sat VARCHAR(50) NULL,
    classroom VARCHAR(255) NULL,
    students_enrolled INTEGER NULL,
    students_dropped INTEGER NULL,
    language VARCHAR(50) NULL,
    notes TEXT NULL,
    with_class VARCHAR(255) NULL,
    experiment VARCHAR(255) NULL,
    cross_discipline VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_courses_year_sem_code UNIQUE (id),
    FOREIGN KEY (department_year_id) REFERENCES department_years (id) ON DELETE CASCADE
);
