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

def _run_coro_sync(coro, timeout: float):
    try:
        asyncio.get_running_loop()
        running = True
    except RuntimeError:
        running = False

    if not running:
        return asyncio.run(asyncio.wait_for(coro, timeout=timeout))

    result_container = {"exc": None, "result": None}

    def _worker():
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
            result_container["result"] = result
        except Exception as e:
            result_container["exc"] = e
        finally:
            try:
                new_loop.close()
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout + 1.0)
    if t.is_alive():
        raise TimeoutError("OCR 작업이 시간 초과로 종료되지 않았습니다.")
    if result_container["exc"] is not None:
        raise result_container["exc"]
    return result_container["result"]

def windows_ocr(pil_img: Image.Image, lang_tag: str, timeout: float = 5.0) -> str:
    async def _ocr_work():
        if not is_ocr_language_supported(lang_tag): return f"해당 언어팩 미설치됨{lang_tag}"
        engine = OcrEngine.try_create_from_language(Language(lang_tag))

        if engine is None: raise RuntimeError(f"OCR 엔진 생성 실패")

        sbmp = _pil_to_sbmp(pil_img)

        result = await engine.recognize_async(sbmp)

        lines = [" ".join(w.text for w in line.words) for line in result.lines]
        return "\n".join(lines).strip()

    return _run_coro_sync(_ocr_work(), timeout=timeout)