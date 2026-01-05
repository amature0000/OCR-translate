import json, os, uuid
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from PyQt5 import QtGui

APP_NAME = "OCR Translate"

def _appdata_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d

DEFAULT_PATH = os.path.join(_appdata_dir(), "settings.json")
ASSET_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

ex_1: str = (
    "너는 FPS 게임 Arena Breakout: Infinite의 공식 번역가다.\n"
    "이름, 지역 등의 고유명사는 번역하지 말고 반드시 영문 그대로 제공하거나 발음을 음차하라.\n"
    "UI 요소, 버튼, 설정 이름 등은 가능한 직역하고 의역하지 마라.\n"
    "아이템, 시스템 옵션, 미션 요구사항 등 인게임 시스템 메시지는 가벼운 경어체로 간결하고 직관적으로 번역하라.\n"
    "미션 스토리, NPC 대사, NPC 메시지, 대화 내용 등에 대해서는 경어체를 절대 사용하지 말고, 상황과 캐릭터에 맞는 자연스럽고 몰입감 있는 말투로 번역하라.\n"
    "NPC 대사에서는 존댓말(하세요, 입니다, 해주세요 등)을 절대 사용하지 말고, 반드시 반말이나 중립적인 구어체로 번역하라.\n"
    "출력 형식은 주어진 문장에 대한 한글 번역만을 담고 있어야 하며, 이외의 단어나 문장이 들어가서는 안 된다.\n"
    "출력할 텍스트가 여러 문단으로 이루어진 경우, 빈 줄을 통해 문단을 구분하라."
)
ex_2: str = (
    "너는 온라인 게임 Liar's Bar의 공식 번역가다.\n"
    "고유명사는 번역하지 말고 반드시 영문 그대로 제공하거나 발음을 음차하라.\n"
    "UI 요소, 버튼, 설정 이름 등은 가능한 직역하고 의역하지 마라.\n"
    "아이템, 시스템 옵션 등 인게임 시스템 메시지는 가벼운 경어체로 간결하고 직관적으로 번역하라.\n"
    "출력 형식은 주어진 문장에 대한 한글 번역만을 담고 있어야 하며, 이외의 단어나 문장이 들어가서는 안 된다.\n"
    "출력할 텍스트가 여러 문단으로 이루어진 경우, 빈 줄을 통해 문단을 구분하라."
)
ex_3: str = (
    "너는 구글 렌즈의 번역 기능 대신 사용될 번역기이다.\n"
    "고유명사는 번역하지 말고 반드시 영문 그대로 제공하거나 음차 후 괄호 안에 원문을 제공하라.\n"
    "UI 요소, 버튼, 설정 이름 등은 가능한 직역하고 의역하지 마라.\n"
    "최대한 간결하고 직관적으로 번역해야 하며, 대화문의 경우 구어적인 표현을 적절히 사용해야 한다.\n"
    "출력 형식은 주어진 문장에 대한 한글 번역만을 담고 있어야 하며, 이외의 단어나 문장이 들어가서는 안 된다.\n"
    "출력할 텍스트가 여러 문단으로 이루어진 경우, 빈 줄을 통해 문단을 구분하라."
)

def _make_default_presets():
    def P(name, body):
        return {"id": uuid.uuid4().hex, "name": name, "system_prompt": body.strip()}
    return [
        P("Arena Breakout", ex_1),
        P("Liar's Bar", ex_2),
        P("일반 번역", ex_3)
    ]

@dataclass
class AppSettings:
    # 1) 핫키
    hotkey_combo: str = "ctrl+shift+c"
    hotkey_rem_combo: str = ""
    use_scroll_detect: bool = True
    # 2) 프롬프트
    prompt_presets: List[Dict] = field(default_factory=_make_default_presets)  # [{id,name,system_prompt}]
    active_preset_id: Optional[str] = None
    # 3) API
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_api_key: str = ""
    use_google_api: bool = True
    
    # 4) overlay
    font_family: str = "Malgun Gothic"
    font_size: int = 14
    use_overlay_layout: bool = True
    
    # 5) info
    no_llm: bool = False
    copy_rule: int = 0 # 0, 1, 2 // 번역전, 번역후, 이미지

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
            self._settings = AppSettings()
            self.save()  # 기본값으로 생성
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._settings = AppSettings(**{**asdict(self._settings), **data})
        except Exception:
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
    def hotkey_rem_combo(self) -> str:
        return self._settings.hotkey_rem_combo
    
    @property
    def use_scroll_detect(self) -> bool:
        return self._settings.use_scroll_detect

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
    def use_google_api(self) -> bool:
        return self._settings.use_google_api

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
    
    @property
    def no_llm(self) -> bool:
        return self._settings.no_llm
    
    @property
    def copy_rule(self) -> int:
        return self._settings.copy_rule
    
    # ---------- setters ----------
    def set_hotkey_combo(self, combo: str):
        self._settings.hotkey_combo = combo

    def set_hotkey_rem_combo(self, combo: str):
        self._settings.hotkey_rem_combo = combo

    def set_use_scroll_detect(self, enabled: bool):
        self._settings.use_scroll_detect = bool(enabled)

    def set_system_prompt(self, prompt: str):
        self._settings.system_prompt = prompt or ""

    def set_gemini(self, model: str, api_key: str):
        if not model:
            raise ValueError("모델을 선택하세요.")
        self._settings.gemini_model = model
        self._settings.gemini_api_key = api_key

    def set_use_google_api(self, enabled:bool):
        self._settings.use_google_api = bool(enabled)

    def set_font(self, family, size):
        family = (family or "").strip()
        if not family: return
        if not(6<= int(size) <= 96): return

        self._settings.font_family = family
        self._settings.font_size = int(size)

    def set_use_overlay_layout(self, enabled: bool):
        self._settings.use_overlay_layout = bool(enabled)

    def set_no_llm(self, enabled: bool):
        self._settings.no_llm = bool(enabled)

    def set_copy_rule(self, rule: int):
        self._settings.copy_rule = int(rule)

    @staticmethod
    def default_settings() -> AppSettings:
        return AppSettings()
    
    def reset_to_defaults(self, persist: bool = False):
        self._settings = AppSettings()
        if persist:
            self.save()

    # ---------- prompt ----------
    def list_presets(self):
        return [PromptPreset(**d) for d in self._settings.prompt_presets]
    
    def set_preset(self, preset_id):
        if not any(d['id'] == preset_id for d in self._settings.prompt_presets):
            raise ValueError("no id")
        self._settings.active_preset_id = preset_id
        self.save()

    def get_preset(self):
        id_ = self._settings.active_preset_id
        for d in self._settings.prompt_presets:
            if d['id'] == id_:
                return d["system_prompt"]
        return None

    def add_preset(self, name, system_prompt):
        p = PromptPreset(uuid.uuid4().hex, name.strip() or "새 프리셋", system_prompt or "")
        self._settings.prompt_presets.append(asdict(p))
        self._settings.active_preset_id = p.id
        self.save()
        return p
    
    def update_preset(self, preset_id, name, system_prompt):
        for d in self._settings.prompt_presets:
            if d['id'] == preset_id:
                if (name != None) and (name != ""):
                    d['name'] = name.strip()
                if (system_prompt != None) and (system_prompt != ""):
                    d['system_prompt'] = system_prompt
                self.save()
                return
        raise ValueError("no id")
    
    def delete_preset(self, preset_id):
        self._settings.prompt_presets = [d for d in self._settings.prompt_presets if d["id"] != preset_id]

        if self._settings.active_preset_id == preset_id:
            self._settings.active_preset_id = None
            if len(self._settings.prompt_presets) != 0:
                self._settings.active_preset_id = self._settings.prompt_presets[0]["id"]
        self.save()
    


@dataclass
class PromptPreset:
    id: str
    name: str
    system_prompt: str