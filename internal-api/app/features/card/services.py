from pathlib import Path

import pymupdf


class CardService:
    def __init__(self, title: str = "職位名稱", name: str = "王曉明"):
        self.title: str = title
        self.name: str = name

    @staticmethod
    def _mm_to_points(mm):
        return (mm * 72) / 25.4

    def export(self) -> bytes:
        title_insert_point = pymupdf.Point(self._mm_to_points(15.798), self._mm_to_points(19.09))
        name_insert_point = pymupdf.Point(self._mm_to_points(10.75), self._mm_to_points(38.402))
        template_pdf_path = str(Path(__file__).parent / "template_empty.pdf")
        font_path = str(Path(__file__).parent / "font.ttc")
        doc = pymupdf.open(template_pdf_path)
        page = doc[0]

        font = pymupdf.Font(fontfile=font_path)
        page.insert_font(fontname="新綜藝體W9", fontbuffer=font.buffer)

        page.insert_text(title_insert_point, self.title, fontname="新綜藝體W9", fontsize=18, color=(0, 0, 0))

        page.insert_text(name_insert_point, self.name, fontname="新綜藝體W9", fontsize=54, color=(0, 0, 0))

        # Save the modified document and close it
        pdf_bytes: bytes = doc.tobytes()

        doc.close()
        return pdf_bytes
