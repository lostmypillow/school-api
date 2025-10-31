SELECT
      [學號] AS uid,
      [姓名] AS cn,
      [新密碼] AS pwd,
      [主要部門] AS main_grp,
      [部門] AS other_grp
FROM
      [使用者]
WHERE
      [狀態] = '1'
      AND(
            LEN(學號) >= 6
            OR 學號 = 'admin'
      )