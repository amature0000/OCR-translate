# settings.py
import json, os
from dataclasses import dataclass, asdict
from typing import Optional

DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".ocr_translate_settings.json")

@dataclass
class AppSettings:
    # 1) 핫키
    hotkey_combo: str = "ctrl+shift+c"
    # 2) 프롬프트
    system_prompt: str = (
        "You are a precise translator. Keep meaning, tone, and inline code.\n"
        "Preserve punctuation and formatting. Return only the translated text."
    )
    # 3) API
    gemini_model: str = "gemini-1.5-pro"
    gemini_api_key: str = ""

class SettingsManager:
    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._settings = AppSettings()
        self.load()

    # ---------- basic I/O ----------
    def load(self):
        if not os.path.exists(self.path):
            self.save()  # 기본값으로 생성
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._settings = AppSettings(**{**asdict(self._settings), **data})
        except Exception:
            # 손상된 경우 백업 후 초기화
            try:
                os.replace(self.path, self.path + ".bak")
            except Exception:
                pass
            self._settings = AppSettings()
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True) if os.path.dirname(self.path) else None
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self._settings), f, ensure_ascii=False, indent=2)

    # ---------- getters ----------
    @property
    def hotkey_combo(self) -> str:
        return self._settings.hotkey_combo

    @property
    def system_prompt(self) -> str:
        return self._settings.system_prompt

    @property
    def api_provider(self) -> str:
        return self._settings.api_provider

    @property
    def gemini_model(self) -> str:
        return self._settings.gemini_model

    @property
    def gemini_api_key(self) -> str:
        return self._settings.gemini_api_key

    # ---------- setters (with minimal validation) ----------
    def set_hotkey_combo(self, combo: str):
        if not combo or "+" not in combo:
            raise ValueError("핫키는 'ctrl+shift+f1' 형식이어야 합니다.")
        self._settings.hotkey_combo = combo

    def set_system_prompt(self, prompt: str):
        self._settings.system_prompt = prompt or ""

    def set_gemini(self, model: str, api_key: str):
        if not model:
            raise ValueError("모델을 선택하세요.")
        self._settings.gemini_model = model
        self._settings.gemini_api_key = api_key

    # ---------- update ----------
    def update(self, *, hotkey_combo: Optional[str]=None, system_prompt: Optional[str]=None,
               gemini_model: Optional[str]=None, gemini_api_key: Optional[str]=None):
        if hotkey_combo is not None:
            self.set_hotkey_combo(hotkey_combo)
        if system_prompt is not None:
            self.set_system_prompt(system_prompt)
        if gemini_model is not None or gemini_api_key is not None:
            self.set_gemini(gemini_model or self.gemini_model, gemini_api_key or self.gemini_api_key)
        self.save()
