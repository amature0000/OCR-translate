import asyncio
from io import BytesIO
from typing import Optional
from PIL import Image

from winsdk.windows.globalization import Language
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

async def _pil_to_softwarebitmap_async(pil_img: Image.Image):
    buf = BytesIO()
    pil_img.save(buf, format="BMP")
    data = buf.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(data)
    await writer.store_async()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    sbmp = await decoder.get_software_bitmap_async()
    return sbmp

async def _run_windows_ocr_async(pil_img: Image.Image, lang_tag: Optional[str]):
    engine = (OcrEngine.try_create_from_language(Language(lang_tag))
              if lang_tag else OcrEngine.try_create_from_user_profile_languages())
    sbmp = await _pil_to_softwarebitmap_async(pil_img)
    result = await engine.recognize_async(sbmp)
    return result

def windows_ocr_sync(pil_img: Image.Image, lang_tag: Optional[str]):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_windows_ocr_async(pil_img, lang_tag))
    finally:
        loop.close()
