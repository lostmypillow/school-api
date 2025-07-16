"""Top level module, a.k.a. this is where all code originates.

If you don't know where to start, start with `src.main`.

.. todo::
According to FastAPI's official full stack template (https://github.com/fastapi/full-stack-fastapi-template/tree/master/backend), this top level module should be `app` instead of `src`.

**If you're interested in refactoring:**

- Rename `src` to `app`, and be sure to change two files:

>- `.vscode/launch.json`: `cwd` key should have value `${workspaceFolder}/app/`.
>- `deploy.sh`: find the `ExecStart=$(pwd)/.venv/bin/fastapi run src/main.py --port $PORT` line and change `src` to `app`.
>- Change all docstring links from /src to /app, now THAT's a challenge. And I'm sorry for that, as of this writing, this system is too unstable for me to risk a rewrite, so `src` it remains for all docstring links.

- Add tests: This has been the most bug-ridden piece of shit I've outputted so far. It desperately needs a rewrite to service classes and add full coverage for testing. Follow the official guide for testing: https://fastapi.tiangolo.com/tutorial/testing/, see `` for my version of service classes.
"""  # noqa: E501
