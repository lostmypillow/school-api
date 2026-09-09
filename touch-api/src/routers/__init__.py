"""所有 API endpoint 都定義在這裡.

.. todo::
    - 在 `` refactor branch 中, 這部分已被移至 `app.api.route_name`, 並**嚴格地**只匯入 service, 再透過 endpoint 對外公開。不同於目前的作法, 現在是將 service 邏輯與路由邏輯混在同一個檔案中。

    - 因此重構要分兩步: 你需要將每個路由檔案中的邏輯, 移到對應的 `app.services.service_name` 中, 然後在 `app.api.route_name` 中匯入並使用。

    - 這也與 `src.database` 的 todo 中所提的重構有關, 因為 `app.api.route_name` 會匯入來自 `app.database.dependencies` 的 FastAPI Depends 函式, 並透過 Depends 注入路由, 然後路由再把 session 傳入需要它的 service。請參考 `` refactor branch 中任一個 route 或 service 檔案以取得更多資訊。


"""  # noqa: E501
