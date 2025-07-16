"""Main entry file of the entire FastAPI app.

From top to bottom of the `src.main` source code:

1. Defines `src.main.lifespan`.
2. Extracts title (key 'name' in `pyproject.toml`), description and version from `pyproject.toml`.
3. Combine them with a key 'lifespan' and value `src.main.lifespan` into `common_kwargs` dictionary.
4. If this FastAPI is being deployed on Linux, disable built-in Swagger, ReDoc and updates root_path. This assumes all deployment will happen on Linux while developing happens on Windows. Now question: I can still access `http://IP_OR_DOMAIN/api/touch/docs` in production, though?
> Answer: Well we DO serve a custom Swagger on "/docs", using `src.main.custom_swagger_ui_html`.
5. Pass the combined kwargs to FastAPI.
6. Defines `src.main.custom_swagger_ui_html` and `src.main.swagger_ui_redirect`.
7. Adds all the routers to FastAPI via `include_router` functions.


.. todo::
**If you're interested in refactoring:**

1. Enforce CORS: right now when adding CORSMiddleware, allow_origins is set to `["*"]`, this is **unsafe** and should be changed to `["FRONTEND_URL"]`. Read this for the 'why': https://fastapi.tiangolo.com/tutorial/cors/.
2. Steps 2 to 4: In ``, these steps have been moved to `app.core.config`, we import the dictionary from that module and still pass it into FastAPI as kwargs. See `ka-tutor-api`'s `app.core.config` to get an idea how to refactor.

"""  # noqa: E501
import logging
import os
import tomllib
from contextlib import asynccontextmanager
from pathlib import Path as pathlib_Path
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from rich.logging import RichHandler
from rich.traceback import install

from .database.exec_sql import async_engine
from .routers import (
    auth,
    seat,
    status,
    survey,
    ws,
)

logger = logging.getLogger("rich")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """Set up Rich logger. Disposes of SQLAlchemy async_engine on shutdown.

    Parameters
    ----------
    app : FastAPI
        FastAPI class, see https://fastapi.tiangolo.com/reference/fastapi/
    .. todo::
    **If you're interested in refactoring:**

    In ``, this entire function (including the @asynccontextmanager decorator) has been moved to `app.core.lifespan`, see `src` for why the path starts with "app" and not "src".

    In ``, the logging logic has also entirely revamped and moved to `app.core.log`, see ``'s `app.core.log` for more information.
    """  # noqa: E501
    install(show_locals=True)
    rich_handler = RichHandler(rich_tracebacks=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
    )
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = [rich_handler]
        logger.setLevel(logging.INFO)



    yield
    if async_engine:
        await async_engine.dispose()
        logger.info("[SHUTDOWN] Disposed async SQLAlchemy Engine")


backend_pyproject_path = (
    pathlib_Path(__file__).resolve().parent.parent / "pyproject.toml"
)
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)

is_linux = os.name == "posix" and os.uname().sysname == "Linux"

common_kwargs = {
    "lifespan": lifespan,
    "title": backend_data.get("project", {}).get("name", "Kw FastAPI Project"),
    "description": backend_data.get("project", {}).get(
        "description", "description here",
    ),
    "version": backend_data.get("project", {}).get("version", "0.0.0"),
}

if is_linux:
    common_kwargs.update(
        {
            "docs_url": None,
            "redoc_url": None,
            "root_path": "/api/touch",
        },
    )

app = FastAPI(**common_kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    """Serve self-hosted Swagger.

    Follows this guide to self host Swagger assets and set up routing: https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/?h=hos#self-hosting-javascript-and-css-for-docs

    Now why is openapi_url set this way instead of just `app.openapi_url`?

    > Well, if we're on Linux and the root_path of the instantiated FastAPI class is '/api/touch', then the openapi.json that Swagger relies on will be served at `http://IP_OR_DOMAIN/api/touch/openapi.json`. Unfortunately `app.openapi_url`'s value is `/openapi.json`, so if we followed the guide completely then Swagger would complain not being able to get API definition from `http://IP_OR_DOMAIN/openapi.json`. That's why we add root_path, so Swagger knows to get OpenAPI definition from `http://IP_OR_DOMAIN/api/touch/openapi.json`.

    Returns
    -------
    HTMLResponse
        The Swagger API Documentation.
    .. todo::
    **If you're interested in refactoring:**

    In ``, this and `src.main.swagger_ui_redirect` has been combined and moved into a single module in `app.api.docs`. See `src` for why the top level module is `app` instead of `src`.


    """  # noqa: E501
    return get_swagger_ui_html(
        openapi_url=app.root_path + cast("str", app.openapi_url),
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/swagger_assets/swagger-ui-bundle.js",
        swagger_css_url="/swagger_assets/swagger-ui.css",
        swagger_favicon_url="/swagger_assets/favicon.ico",
    )


@app.get(cast("str", app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    """Honestly don't know what this does, but it was present in the official guide that I followed: https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/?h=hos#self-hosting-javascript-and-css-for-docs.

    Returns
    -------
    HTMLResponse
        Unknown for now.

    .. todo::
    If you come across this and you **do** know what this is for, please update the docstrings.

    See `src.main.custom_swagger_ui_html` for refactoring tips.
    """  # noqa: E501
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(status.router)

app.include_router(auth.router)

app.include_router(ws.router)

app.include_router(seat.router)

app.include_router(survey.router)
