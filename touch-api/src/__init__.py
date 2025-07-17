"""所有程式碼的起點.

如果你不知道從哪開始看, 請從 `src.main` 開始.

.. todo::

    - **將 `src` 更名為 `app`:**

        - 為什麼? 根據 FastAPI 官方的 full stack 模板 (https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend) , 最上層模組應該命名為 `app` 而非 `src`.
        - 請務必修改以下三個檔案:

            - `.vscode/launch.json`:`cwd` 鍵的值應為 `${workspaceFolder}/app/`.
            - `.vscode/tasks.json`:在標籤為 "Generate docs with pdoc" 的 task 中, 將 `src` 改為 `app`.
            - `deploy.sh`:找到 `ExecStart=$(pwd)/.venv/bin/fastapi run src/main.py --port $PORT` 這一行, 將 `src` 改為 `app`.

        - 將所有 docstring 中的連結從 `src.x` 改為 `app.x`, 這才是真正的挑戰.很抱歉, 目前這個系統太不穩定, 我無法冒險重新改寫, 因此 docstring 中的連結仍然維持為 `src`.

    - **新增測試:**

        - 這是我寫過最多錯誤的爛程式碼, 急需重構為 service class 並補上完整的測試覆蓋率.
        - 請參考 `` 中我實作的 service class.
        - 按照官方測試指南進行:https://fastapi.tiangolo.com/tutorial/testing/

    - **修復所有 linting 問題:**

        - 如果你在 VSCode 中完全依照我在 README 中所寫的設定工具, 在 `Problems` 標籤頁中會顯示所有的 ruff lint 錯誤.
        - 點擊每個檔案確認 VSCode 是否都能正確偵測, 或是執行 VSCode 的任務 `Ruff: check + safe fix` 看是否還有未修復的錯誤.



"""  # noqa: E501
