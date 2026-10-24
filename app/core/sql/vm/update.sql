UPDATE
    vm_details
SET
    vm_name = ?,
    human_owner = ?,
    pc_owner = ?,
    pve = ?,
    pve_host = ?,
    pve_token_username = ?,
    pve_token_name = ?,
    pve_token_value = ?,
    pve_vm_id = ?,
    pve_proxy = ?,
    spice_proxy = ?,
    vm_password = ?,
    usb = ?,
    updated_at = SYSDATETIME()
WHERE
    id = ?;
