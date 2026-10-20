select
    id,
    name,
    city
from schools
where school_type = $1
