DROP TABLE IF EXISTS vm_details;

CREATE TABLE vm_details (
    id SERIAL PRIMARY KEY,
    vm_name VARCHAR(100) NOT NULL,
    human_owner VARCHAR(100) NULL,
    pc_owner VARCHAR(100) NULL,
    pve BOOLEAN NOT NULL,
    pve_host VARCHAR(150) NULL,
    pve_token_username VARCHAR(100) NULL,
    pve_token_name VARCHAR(100) NULL,
    pve_token_value VARCHAR(36) NULL,
    pve_vm_id INT NULL,
    pve_proxy VARCHAR(150) NULL,
    spice_proxy VARCHAR(150) NOT NULL,
    vm_password VARCHAR(128) NULL,
    usb BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_proxmox CHECK (pve IN (0, 1)),
    CONSTRAINT chk_optional_fields CHECK (
        pve = 0
        OR (
            pve_host IS NOT NULL
            AND pve_token_username IS NOT NULL
            AND pve_token_name IS NOT NULL
            AND pve_token_value IS NOT NULL
            AND pve_vm_id IS NOT NULL
        )
    ),
    CONSTRAINT uq_vm_name UNIQUE (vm_name)
);

INSERT INTO
vm_details (
    vm_name,
    human_owner,
    pc_owner,
    pve,
    pve_host,
    pve_token_username,
    pve_token_name,
    pve_token_value,
    pve_vm_id,
    pve_proxy,
    spice_proxy,
    vm_password,
    usb,
    created_at
)
VALUES
(
    'Win10',
    '201350',
    NULL,
    1,
    '192.168.2.13:8006',
    'lostmypillow',
    'lostmypillow',
    '245a4a7a-581f-434d-be48-e393d9578aa0',
    301,
    'pve3.kaowei.tw:3128',
    '192.168.2.13:3128',
    NULL,
    0,
    CURRENT_TIMESTAMP
);

INSERT INTO
vm_details (
    vm_name,
    human_owner,
    pc_owner,
    pve,
    pve_host,
    pve_token_username,
    pve_token_name,
    pve_token_value,
    pve_vm_id,
    pve_proxy,
    spice_proxy,
    vm_password,
    usb,
    created_at
)
VALUES
(
    'hanWin7',
    '200829',
    NULL,
    0,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    '192.168.2.21:8283',
    '8283',
    0,
    CURRENT_TIMESTAMP
);
