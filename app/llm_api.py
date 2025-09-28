from __future__ import annotations

import time
from typing import Iterable, List, Optional

import google.generativeai as genai
from settings import SettingsManager


class LLMError(RuntimeError):
    """LLM 호출 실패를 표현하는 예외."""
    pass


class LLMClient:
    """
    Gemini 호출 래퍼.
    - settings.system_prompt  → Commands (system_instruction)
    - 입력 텍스트             → "Text to Translate:\n{ocr_text}"
    """
    def __init__(
        self,
        settings: SettingsManager,
        *,
        temperature: float = 0.2,
        max_retries: int = 3,
        retry_base_delay: float = 0.8,
        request_timeout: Optional[float] = None,  # SDK 전역 타임아웃은 없으나, 내부적으로 사용 가능
    ):
        self._settings = settings
        self._temperature = float(temperature)
        self._max_retries = int(max_retries)
        self._retry_base_delay = float(retry_base_delay)
        self._timeout = request_timeout

        self._model = None
        self._configure()

    # -------------------- public API --------------------

    def translate(self, ocr_text: str) -> str:
        """
        OCR 텍스트를 받아 번역 결과 문자열을 반환.
        실패 시 LLMError 발생.
        """
        if not isinstance(ocr_text, str):
            raise TypeError("ocr_text는 문자열이어야 합니다.")
        payload = self._build_user_payload(ocr_text)
        resp = self._call_with_retries(payload)
        return self._extract_text(resp)

    # -------------------- internal helpers --------------------

    def _configure(self):
        api_key = (self._settings.gemini_api_key or "").strip()
        model_name = (self._settings.gemini_model or "").strip()
        sys_prompt = (self._settings.system_prompt or "").strip()

        genai.configure(api_key=api_key)
        # system_instruction 에 Commands 내용을 그대로 넣음
        self._model = genai.GenerativeModel(
            model_name,
            system_instruction=sys_prompt if sys_prompt else None
        )

    def _build_user_payload(self, ocr_text: str):
        return f"Text to Translate:\n{ocr_text}"

    def _call_with_retries(self, user_payload: str):
        """
        간단한 재시도(backoff) 포함. SDK 오류 메시지를 LLMError로 래핑.
        """
        last_err: Optional[Exception] = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._model.generate_content(
                    user_payload,
                    generation_config={
                        "temperature": self._temperature,
                    },
                    safety_settings=None,
                )
                return resp
            except Exception as e:
                last_err = e
                if attempt >= self._max_retries:
                    break
                time.sleep(self._retry_base_delay * (2 ** (attempt - 1)))
        raise LLMError(f"Gemini 호출 실패: {last_err}")

    @staticmethod
    def _extract_text(resp) -> str:

        text = getattr(resp, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        try:
            cand0 = resp.candidates[0]
            parts = getattr(cand0, "content", None).parts  # type: ignore[attr-defined]
            buf = []
            for p in parts:
                t = getattr(p, "text", None)
                if t:
                    buf.append(t)
            joined = "\n".join(buf).strip()
            if joined:
                return joined
        except Exception:
            pass

        return str(resp)
