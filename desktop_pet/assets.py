from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QTransform

from desktop_pet.art import DEFAULT_ASSET_SIZE, ensure_default_assets


ASSET_DIR = Path(__file__).resolve().parent / "assets"


class PetSpriteStore:
    def __init__(self, scale: float) -> None:
        ensure_default_assets(ASSET_DIR)
        self.scale = scale
        self.base_size = DEFAULT_ASSET_SIZE
        self.render_size = max(72, int(self.base_size * scale))
        self._base = {}

    def frame_size(self) -> tuple[int, int]:
        return self.render_size, self.render_size

    def pixmap(self, mood: str, edge: str, direction: int) -> QPixmap:
        base = self._load(mood)
        pixmap = base.scaled(
            self.render_size,
            self.render_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        if edge == "top":
            pixmap = pixmap.transformed(QTransform().rotate(180), Qt.TransformationMode.SmoothTransformation)
            if direction < 0:
                pixmap = _mirror(pixmap, horizontal=True)
            return pixmap
        if edge == "left":
            pixmap = pixmap.transformed(QTransform().rotate(90), Qt.TransformationMode.SmoothTransformation)
            if direction > 0:
                pixmap = _mirror(pixmap, vertical=True)
            return pixmap
        if edge == "right":
            pixmap = pixmap.transformed(QTransform().rotate(270), Qt.TransformationMode.SmoothTransformation)
            if direction < 0:
                pixmap = _mirror(pixmap, vertical=True)
            return pixmap
        if direction > 0:
            pixmap = _mirror(pixmap, horizontal=True)
        return pixmap

    def _load(self, mood: str) -> QPixmap:
        mood_key = mood if mood in {"idle", "peek", "react", "sleep", "blink"} else "idle"
        if mood_key not in self._base:
            self._base[mood_key] = QPixmap(str(ASSET_DIR / f"pet_{mood_key}.png"))
        return self._base[mood_key]


def _mirror(pixmap: QPixmap, horizontal: bool = False, vertical: bool = False) -> QPixmap:
    image = pixmap.toImage().mirrored(horizontal, vertical)
    return QPixmap.fromImage(image)
