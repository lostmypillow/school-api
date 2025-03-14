DROP TABLE IF EXISTS vm_details;

CREATE TABLE vm_details (
    id INT IDENTITY(1, 1) PRIMARY KEY,
    vm_name NVARCHAR(100) NOT NULL,
    human_owner NVARCHAR(100) NULL,
    pc_owner NVARCHAR(100) NULL,
    pve BIT NOT NULL,
    pve_host NVARCHAR(150) NOT NULL,
    pve_token_username NVARCHAR(100) NULL,
    pve_token_name NVARCHAR(100) NULL,
    pve_token_value NVARCHAR(36) NULL,
    pve_vm_id INT NULL,
    pve_proxy NVARCHAR(150) NULL,
    spice_proxy NVARCHAR(150) NOT NULL,
    vm_password NVARCHAR(128) NULL,
    created_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL,
    updated_at DATETIME2 DEFAULT SYSDATETIME() NOT NULL,
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
    CONSTRAINT uq_pve_vm_id UNIQUE (pve_vm_id),
    -- Ensure pve_vm_id is unique
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
        created_at
    )
VALUES
    (
        'Win10',
        '201350',
        NULL,
        1,
        '192.168.2.13:8006' 'lostmypillow',
        'lostmypillow',
        '245a4a7a-581f-434d-be48-e393d9578aa0',
        -- Example UUID
        301,
        'pve1.kaowei.tw:3128',
        '192.168.2.13:3128',
        NULL,
        SYSDATETIME()
    );