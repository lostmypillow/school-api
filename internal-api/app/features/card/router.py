from fastapi import APIRouter
from fastapi.responses import Response

from app.features.card.services import CardService

router = APIRouter(prefix="/card", tags=["Card Generation"])


@router.get("")
async def generate_card(title: str = "職位名稱", name: str = "王曉明"):
    service = CardService(title=title, name=name)
    pdf_bytes = service.export()
    headers = {
        'Content-Disposition': 'inline; filename="output.pdf"'  # Use 'attachment' to force a download dialog
    }

    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers=headers
    )
