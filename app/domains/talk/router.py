from urllib.parse import unquote

import chardet
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.domains.talk.dependencies import get_message_service
from app.domains.talk.services import NextcloudService

router = APIRouter(prefix="/talk", tags=["Nextcloud Talk bridge"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Send a message via Nextcloud",
    description=(
            "Sends a message through the Nextcloud service using query parameters. "
            "All fields are required, including the password."
    ),
    responses={
        200: {
            "content": {
                "text/html": {
                    "example": """
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
</head>
<body>
    <h1>Success</h1>
</body>
</html>
"""
                }
            },
            "description": "HTML 格式的成功頁面",
        },
        400: {"description": "Invalid request"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"},
    },
)
async def send_message(
        background_tasks: BackgroundTasks,
        sender: str = Query(..., description="Username or email of the sender"),
        recipient: str = Query(..., description="Username or email of the recipient"),
        message: str = Query(..., description="Content of the message to send"),
        password: str = Query(..., description="Password for authentication or encryption"),
        service: NextcloudService = Depends(get_message_service),
):
    """
    Send a message using the Nextcloud messaging service.

    **Query Parameters:**
    - `sender`: The username or email of the sender
    - `recipient`: The username or email of the recipient
    - `message`: The message body to send
    - `password`: Required password for authentication or encryption
    """
    try:
        encoding = chardet.detect(unquote(message).encode())["encoding"]
        if encoding:
           decoded_message = unquote(message).encode().decode(encoding=encoding)
        else:
            raise ValueError
        background_tasks.add_task(service.send_message, sender, recipient, decoded_message, password)
        return HTMLResponse("""<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
</head>
<body>
    <h1>Success</h1>
</body>
</html>
""")

    except ValueError as v:
        raise HTTPException(status_code=400, detail=str(v)) from v
    except PermissionError as p:
        raise HTTPException(status_code=401, detail="Unauthorized access") from p
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e

