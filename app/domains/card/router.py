import json
from pathlib import Path
from typing import List

import pymupdf  # PyMuPDF
from fastapi import APIRouter
from fastapi.responses import Response


def _mm_to_points(mm):
    return (mm * 72) / 25.4


def generate_bytes(title: str, name: str) -> bytes:
    title_insert_point = pymupdf.Point(_mm_to_points(15.798), _mm_to_points(19.09))
    name_insert_point = pymupdf.Point(_mm_to_points(10.75), _mm_to_points(38.402))
    template_pdf_path = str(Path(__file__).parent / "template_empty.pdf")
    font_path = str(Path(__file__).parent / "font.ttc")
    doc = pymupdf.open(template_pdf_path)
    page = doc[0]

    font = pymupdf.Font(fontfile=font_path)
    page.insert_font(fontname="新綜藝體W9", fontbuffer=font.buffer)

    page.insert_text(title_insert_point, title, fontname="新綜藝體W9", fontsize=18, color=(0, 0, 0))

    page.insert_text(name_insert_point, name, fontname="新綜藝體W9", fontsize=54, color=(0, 0, 0))

    pdf_bytes: bytes = doc.tobytes()

    doc.close()
    return pdf_bytes


def generate_a4(cards_bytes: List[bytes]) -> bytes:
    if len(cards_bytes) > 10:
        raise ValueError("This template only supports up to 10 cards per A4 sheet.")

    a4_width = 595.27
    a4_height = 841.89
    card_width = 3.5 * 72  # 252 points
    card_height = 2.0 * 72  # 144 points

    margin_x = (a4_width - (card_width * 2)) / 2
    margin_y = (a4_height - (card_height * 5)) / 2

    out_doc = pymupdf.open()
    page = out_doc.new_page(width=a4_width, height=a4_height)

    card_index = 0

    for row in range(5):
        for col in range(2):
            # Stop if we've placed all the cards provided in the array
            if card_index >= len(cards_bytes):
                break

            x0 = margin_x + (col * card_width)
            y0 = margin_y + (row * card_height)
            rect = pymupdf.Rect(x0, y0, x0 + card_width, y0 + card_height)

            # Open the specific card's bytes from the array
            src_doc = pymupdf.open("pdf", cards_bytes[card_index])

            page.show_pdf_page(rect, src_doc, 0)
            src_doc.close()

            card_index += 1

    pdf_bytes = out_doc.tobytes()
    out_doc.close()

    return pdf_bytes


router = APIRouter(prefix="/card", tags=["Card Generation"])


class Card:
    title: str = "職位名稱"
    name: str = "王曉明"


@router.get("")
async def generate_card(data: str):
    list_dict = json.loads(data)
    card_bytes = []
    for card in list_dict:
        card_bytes.append(generate_bytes(name=card["name"], title=card["title"]))

    pdf_bytes = generate_a4(card_bytes)
    headers = {
        'Content-Disposition': 'inline; filename="output.pdf"'  # Use 'attachment' to force a download dialog
    }

    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers=headers
    )
