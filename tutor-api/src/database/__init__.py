"""與資料庫相關的函式與變數.

.. todo::
    在 refactor branch 中, 這個資料夾不是單一檔案, 而是由三個檔案構成: `dependencies.py`, `engine.py`, `exec_sql.py`

    基本上你可以將目前 `src.database.exec_sql` 中的 FastAPI Depends 相容函式與 `engine` 變數抽出來. 另一種做法是直接從 refactor branch 的 `app.database` 中複製上述三個檔案過來, 基本上應該可以運作……但目前還不行.

    目前的 `exec_sql` 函式 (也就是 `src.database.exec_sql` 檔案中名為 'exec_sql' 的函式), 是一個**不需要**傳入 session 的函式.

    然而, 在 refactor branch 中的 exec_sql 函式則**需要** session. 該 session 可以透過 FastAPI 的 Depends() 包裹 `app.database.dependencies.get_session` 函式取得, 也可以直接呼叫該函式來取得 session. 在 refactor branch 中, 我是在 router 端使用 Depends 取得 session, 並傳入 service class.

    簡而言之, 要注意新的 `exec_sql` 函式 (位於 refactor branch 的 `app.database.exec_sql` 模組中) 需要額外的 `session` 參數, 其型別為 `sqlalchemy.ext.asyncio.AsyncSession`, 而這是一個**必要**參數.

這裡我想跟你分享一個小祕密。我對自己把每個 microservice（touch、tutor、vm、trials）拆分成獨立 repo 的做法，其實有點不太滿意。前端拆分成各自的 repo 還說得過去，但 API 端每個 service 拆成一個 repo，結果只是讓每個 repo 都擁有幾乎一模一樣的 database 模組與重複程式碼。

反正正式環境的路由是透過 caddy 的子資料夾處理的，所以每個 microservice（tutor、touch、vm、sms）*其實可以*只是獨立的 APIRouter，而不是獨立的 repo。這樣一來，所有路由都能共用同一個 `src.database` 模組，重複程式碼也就能重用。

但這會是一次很大的重構，而且會對最關鍵的 service（sms）造成風險，所以我甚至連動手都還沒開始。但在我看來，這是個必要的重構，只是需要足夠時間來測試而已。



"""  # noqa: E501
