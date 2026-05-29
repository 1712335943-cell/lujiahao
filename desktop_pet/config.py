from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


APP_DIR = Path.home() / ".desktop_pet"
CONFIG_PATH = APP_DIR / "settings.json"


@dataclass
class PetSettings:
    scale: float = 0.72
    speed: int = 2
    activity_interval_ms: int = 2600
    click_through: bool = False
    always_on_top: bool = True
    muted: bool = True
    auto_hide_fullscreen: bool = True
    behavior_mode: str = "normal"
    edge: str = "right"
    offset: int = 180


def load_settings() -> PetSettings:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        return PetSettings()

    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return PetSettings()

    settings = PetSettings()
    for key, value in payload.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings


def save_settings(settings: PetSettings) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(asdict(settings), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
