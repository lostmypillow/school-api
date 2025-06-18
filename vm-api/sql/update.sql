UPDATE
    vm_details
SET
    vm_name = :vm_name,
    human_owner = :human_owner,
    pc_owner= :pc_owner,
    pve = :pve,
    pve_host = :pve_host,
    pve_token_username = :pve_token_username,
    pve_token_name = :pve_token_name,
    pve_token_value = :pve_token_value,
    pve_vm_id = :pve_vm_id,
    pve_proxy = :pve_proxy,
    spice_proxy  = :spice_proxy,
    vm_password = :vm_password,
    usb =:usb,
    updated_at = SYSDATETIME()
WHERE
    id = :id;