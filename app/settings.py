import json, os
from dataclasses import dataclass, asdict
from typing import Optional
from PyQt5 import QtGui

APP_NAME = "OCR Translate"

def _appdata_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d

DEFAULT_PATH = os.path.join(_appdata_dir(), "settings.json")
ASSET_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

@dataclass
class AppSettings:
    # 1) 핫키
    hotkey_combo: str = "ctrl+shift+c"
    # 2) 프롬프트
    system_prompt: str = (
        "너는 FPS 게임 Arena Breakout: Infinite의 공식 번역가다.\n"
        "이름, 지역 등의 고유명사는 번역하지 말고 반드시 영문 그대로 제공하거나 발음을 음차하라.\n"
        "UI 요소, 버튼, 설정 이름 등은 가능한 직역하고 의역하지 마라.\n"
        "아이템, 시스템 옵션, 미션 요구사항 등 인게임 시스템 메시지는 가벼운 경어체로 간결하고 직관적으로 번역하라.\n"
        "미션 스토리, NPC 대사, NPC 메시지, 대화 내용 등에 대해서는 경어체를 절대 사용하지 말고, 상황과 캐릭터에 맞는 자연스럽고 몰입감 있는 말투로 번역하라.\n"
        "NPC 대사에서는 존댓말(하세요, 입니다, 해주세요 등)을 절대 사용하지 말고, 반드시 반말이나 중립적인 구어체로 번역하라.\n"
        "출력 형식은 주어진 문장에 대한 한글 번역만을 담고 있어야 하며, 이외의 단어나 문장이 들어가서는 안 된다.\n"
        "출력할 텍스트가 여러 문단으로 이루어진 경우, 빈 줄을 통해 문단을 구분하라."
    )
    # 3) API
    gemini_model: str = "gemini-2.5-flash-lite-preview-06-17"
    gemini_api_key: str = ""
    
    # 4) overlay
    font_family: str = "Malgun Gothic"
    font_size: int = 14
    use_overlay_layout: bool = True

class SettingsManager:
    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._settings = AppSettings()
        self._asset_font_families = []  # assets/fonts 에서 로드된 family 목록
        self._load_asset_fonts()
        self.load()

    # ---------- asset fonts ----------
    def _load_asset_fonts(self):
        self._asset_font_families.clear()
        if not os.path.isdir(ASSET_FONTS_DIR):
            return
        for fn in os.listdir(ASSET_FONTS_DIR):
            if not fn.lower().endswith((".ttf", ".otf", ".ttc", ".otc")):
                continue
            p = os.path.join(ASSET_FONTS_DIR, fn)
            try:
                fid = QtGui.QFontDatabase.addApplicationFont(p)
                if fid != -1:
                    fams = QtGui.QFontDatabase.applicationFontFamilies(fid)
                    self._asset_font_families.extend(fams)
            except Exception:
                pass

        self._asset_font_families = sorted(set(self._asset_font_families))

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
    def gemini_model(self) -> str:
        return self._settings.gemini_model

    @property
    def gemini_api_key(self) -> str:
        return self._settings.gemini_api_key

    @property
    def font_family(self) -> str:
        return self._settings.font_family
    
    @property
    def font_size(self) -> int:
        return self._settings.font_size

    @property
    def asset_font_families(self):
        return list(self._asset_font_families)
    
    @property
    def use_overlay_layout(self) -> bool:
        return self._settings.use_overlay_layout
    
    # ---------- setters ----------
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

    def set_font(self, family, size):
        family = (family or "").strip()
        if not family: return
        if not(6<= int(size) <= 96): return

        self._settings.font_family = family
        self._settings.font_size = int(size)

    def set_use_overlay_layout(self, enabled: bool):
        self._settings.use_overlay_layout = bool(enabled)

    def update(self, *, hotkey_combo: Optional[str]=None, system_prompt: Optional[str]=None,
               gemini_model: Optional[str]=None, gemini_api_key: Optional[str]=None,
               font_family: Optional[str]=None, font_size: Optional[int]=None,
               use_overlay_layout: Optional[bool]=None):
        if hotkey_combo is not None:
            self.set_hotkey_combo(hotkey_combo)
        if system_prompt is not None:
            self.set_system_prompt(system_prompt)
        if gemini_model is not None or gemini_api_key is not None:
            self.set_gemini(gemini_model or self.gemini_model, gemini_api_key or self.gemini_api_key)
        if (font_family is not None) or (font_size is not None):
            self.set_font(font_family or self.font_family, font_size or self.font_size)
        if use_overlay_layout is not None:
            self.set_use_overlay_layout(use_overlay_layout)
        self.save()
        
    @staticmethod
    def default_settings() -> AppSettings:
        return AppSettings()
    
    def reset_to_defaults(self, persist: bool = False):
        self._settings = AppSettings()
        if persist:
            self.save()
