"""與資料庫相關的函式與變數.

.. todo::
    在 `` 中, 這個資料夾不是單一檔案, 而是由三個檔案構成: `dependencies.py`, `engine.py`, `exec_sql.py`

    基本上你可以將目前 `src.database.exec_sql` 中的 FastAPI Depends 相容函式與 `engine` 變數抽出來. 另一種做法是直接從 `` 的 `app.database` 中複製上述三個檔案過來, 基本上應該可以運作……但目前還不行.

    目前的 `exec_sql` 函式 (也就是 `src.database.exec_sql` 檔案中名為 'exec_sql' 的函式), 是一個**不需要**傳入 session 的函式.

    然而, 在 `` 中的 exec_sql 函式則**需要** session. 該 session 可以透過 FastAPI 的 Depends() 包裹 `app.database.dependencies.get_session` 函式取得, 也可以直接呼叫該函式來取得 session. 在 `` 中, 我是在 router 端使用 Depends 取得 session, 並傳入 service class.

    簡而言之, 要注意新的 `exec_sql` 函式 (位於 `` 的 `app.database.exec_sql` 模組中) 需要額外的 `session` 參數, 其型別為 `sqlalchemy.ext.asyncio.AsyncSession`, 而這是一個**必要**參數.


"""  # noqa: E501

