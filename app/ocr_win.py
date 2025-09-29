import asyncio
from PIL import Image
import threading

from winsdk.windows.globalization import Language
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.graphics.imaging import (
    BitmapPixelFormat, SoftwareBitmap, BitmapAlphaMode
)
from winsdk.windows.storage.streams import DataWriter


def is_ocr_language_supported(lang_tag: str) -> bool:
    try:
        return bool(OcrEngine.is_language_supported(Language(lang_tag)))
    except Exception:
        return False
    
def _pil_to_sbmp(pil_img: Image.Image) -> SoftwareBitmap:
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")

    w, h = pil_img.size
    bgra_bytes = pil_img.tobytes("raw", "BGRA")
    assert len(bgra_bytes) == w * h * 4

    writer = DataWriter()
    try:
        writer.write_bytes(bgra_bytes)
    except TypeError:
        from array import array
        writer.write_bytes(array('B', bgra_bytes))
    ibuf = writer.detach_buffer()

    sbmp = SoftwareBitmap.create_copy_from_buffer(
        ibuf,
        BitmapPixelFormat.BGRA8,
        w, h,
        BitmapAlphaMode.IGNORE
    )
    return sbmp

_bg_loop = None
_bg_thread = None

def _make_bg_loop():
    global _bg_loop, _bg_thread
    if _bg_loop is not None:
        return _bg_loop
    ready = threading.Event()

    def _worker():
        global _bg_loop
        _bg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bg_loop)
        ready.set()
        _bg_loop.run_forever()
        _bg_loop.close()

    _bg_thread = threading.Thread(target=_worker, name="ocr-translator-OCRLOOP", daemon=True)
    _bg_thread.start()
    ready.wait()
    return _bg_loop

def _run_coro_sync(coro, timeout: float):
    loop = _make_bg_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout=timeout)

def windows_ocr(pil_img: Image.Image, lang_tag: str, timeout: float = 3.0) -> str:
    async def _ocr_work():
        if not is_ocr_language_supported(lang_tag): return f"해당 언어팩 미설치됨{lang_tag}"
        engine = OcrEngine.try_create_from_language(Language(lang_tag))

        if engine is None: raise RuntimeError(f"OCR 엔진 생성 실패")

        sbmp = _pil_to_sbmp(pil_img)

        result = await engine.recognize_async(sbmp)

        lines = [" ".join(w.text for w in line.words) for line in result.lines]
        return "\n".join(lines).strip()

    return _run_coro_sync(_ocr_work(), timeout=timeout)