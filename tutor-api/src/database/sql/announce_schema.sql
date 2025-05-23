CREATE TABLE math_announcements (
    id INT IDENTITY(1, 1) PRIMARY KEY,
    content NVARCHAR(MAX) NOT NULL,
    author CHAR (7) NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL
);