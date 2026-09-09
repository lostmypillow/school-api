UPDATE
    dbo.預約輔導
SET
    下課時間 = GETDATE()
WHERE
    自動編號 = :reservation_id