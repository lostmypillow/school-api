UPDATE
    vm_details
SET
    vm_name = $1,
    human_owner = $2,
    pc_owner = $3,
    pve = $4,
    pve_host = $5,
    pve_token_username = $6,
    pve_token_name = $7,
    pve_token_value = $8,
    pve_vm_id = $9,
    pve_proxy = $10,
    spice_proxy = $11,
    vm_password = $12,
    usb = $13,
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = $14;
