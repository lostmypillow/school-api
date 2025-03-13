SELECT
    *
FROM
    vm_details
WHERE
    human_owner = :request_owner
    OR pc_owner = :request_owner