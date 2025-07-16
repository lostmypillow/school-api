"""Database related functions and variables.

.. todo::
**If you're interested in refactoring:**

In ``, this folder has 3 files instead of 1: 
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----           7/16/2025  6:15 PM                sql
-a---           7/16/2025  6:15 PM              0 __init__.py
-a---           7/16/2025  6:15 PM            313 dependencies.py
-a---           7/16/2025  6:15 PM            671 engine.py
-a---           7/16/2025  6:15 PM           2068 exec_sql.py
```
Basically what you can do is extract the FastAPI Depends compatible function and the engine variable from the current `src.database.exec_sql`. Alternatively, just copy the same 3 files from ``'s `app.database` and it should work...not yet.

Our current `exec_sql` function, yes I mean the function named 'exec_sql' in the file `src.database.exec_sql`, is a function that does not need to pass a session in order to use it. 

The exec_sql from ``, **however**, requires a session. That session will either come from wrapping function in `app.database.dependencies.get_session` in FastAPI Depends() OR using the function directly to get a session. In ``, I use Depends to get the session at the router, and pass it into the service class.

Long story short, watch out for the extra parameter 'session' of type `sqlalchemy.ext.asyncio.AsyncSession` in the new exec_sql function of ``'s `app.database.exec_sql` module, it's a **required** parameter.
"""  # noqa: E501
