 select
	name
from
	.dbo.users
where
	是業務 = 1
	AND 狀態 = 1
	AND LEN(student_id) >= 6