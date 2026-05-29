from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap


DEFAULT_ASSET_SIZE = 180
MOODS = ("idle", "peek", "react", "sleep", "blink")


def ensure_default_assets(asset_dir: Path) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    for mood in MOODS:
        target = asset_dir / f"pet_{mood}.png"
        if target.exists():
            continue
        pixmap = create_pet_asset(DEFAULT_ASSET_SIZE, mood)
        pixmap.save(str(target), "PNG")


def create_pet_asset(size: int, mood: str) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    outline = QColor("#2b2221")
    hair = QColor("#8d7c82")
    hair_shadow = QColor("#78686e")
    skin = QColor("#fff4eb")
    blush = QColor("#f4aab0")
    robe_outer = QColor("#a8d4d7")
    robe_shadow = QColor("#8ebfc1")
    robe_inner = QColor("#f9f8f5")
    sash = QColor("#56546a")
    crown = QColor("#2b2221")

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    _draw_back_hair(p, size, hair_shadow, outline)
    _draw_arms(p, size, robe_outer, robe_inner, outline)
    _draw_robe(p, size, robe_outer, robe_shadow, robe_inner, sash, outline)
    _draw_head(p, size, skin, outline)
    _draw_front_hair(p, size, hair, outline, crown)
    _draw_face(p, size, mood, blush, outline)
    _draw_feet(p, size, outline)

    p.end()
    return pixmap


def _draw_back_hair(p: QPainter, size: int, hair_shadow: QColor, outline: QColor) -> None:
    p.save()
    p.setPen(QPen(outline, 3))
    p.setBrush(hair_shadow)
    left = QPainterPath()
    left.moveTo(size * 0.30, size * 0.30)
    left.quadTo(size * 0.18, size * 0.50, size * 0.25, size * 0.84)
    left.quadTo(size * 0.32, size * 0.77, size * 0.38, size * 0.57)
    left.closeSubpath()
    right = QPainterPath()
    right.moveTo(size * 0.70, size * 0.30)
    right.quadTo(size * 0.82, size * 0.50, size * 0.75, size * 0.84)
    right.quadTo(size * 0.68, size * 0.77, size * 0.62, size * 0.57)
    right.closeSubpath()
    p.drawPath(left)
    p.drawPath(right)
    p.restore()


def _draw_arms(
    p: QPainter,
    size: int,
    robe_outer: QColor,
    robe_inner: QColor,
    outline: QColor,
) -> None:
    p.save()
    p.setPen(QPen(outline, 3))
    p.setBrush(robe_outer)

    left = QPainterPath()
    left.moveTo(size * 0.35, size * 0.54)
    left.quadTo(size * 0.19, size * 0.57, size * 0.12, size * 0.70)
    left.lineTo(size * 0.22, size * 0.72)
    left.quadTo(size * 0.28, size * 0.60, size * 0.39, size * 0.57)
    left.closeSubpath()

    right = QPainterPath()
    right.moveTo(size * 0.65, size * 0.54)
    right.quadTo(size * 0.81, size * 0.57, size * 0.88, size * 0.70)
    right.lineTo(size * 0.78, size * 0.72)
    right.quadTo(size * 0.72, size * 0.60, size * 0.61, size * 0.57)
    right.closeSubpath()

    p.drawPath(left)
    p.drawPath(right)

    p.setBrush(robe_inner)
    p.drawRoundedRect(QRectF(size * 0.10, size * 0.69, size * 0.05, size * 0.03), 3, 3)
    p.drawRoundedRect(QRectF(size * 0.85, size * 0.69, size * 0.05, size * 0.03), 3, 3)
    p.restore()


def _draw_robe(
    p: QPainter,
    size: int,
    robe_outer: QColor,
    robe_shadow: QColor,
    robe_inner: QColor,
    sash: QColor,
    outline: QColor,
) -> None:
    p.save()
    p.setPen(QPen(outline, 3))
    p.setBrush(robe_outer)

    robe = QPainterPath()
    robe.moveTo(size * 0.32, size * 0.53)
    robe.quadTo(size * 0.50, size * 0.47, size * 0.68, size * 0.53)
    robe.lineTo(size * 0.76, size * 0.89)
    robe.quadTo(size * 0.50, size * 0.97, size * 0.24, size * 0.89)
    robe.closeSubpath()
    p.drawPath(robe)

    p.setBrush(robe_shadow)
    p.drawRoundedRect(QRectF(size * 0.27, size * 0.71, size * 0.46, size * 0.17), 12, 12)

    p.setBrush(robe_inner)
    lapel = QPainterPath()
    lapel.moveTo(size * 0.40, size * 0.55)
    lapel.lineTo(size * 0.50, size * 0.68)
    lapel.lineTo(size * 0.60, size * 0.55)
    lapel.lineTo(size * 0.63, size * 0.87)
    lapel.quadTo(size * 0.50, size * 0.92, size * 0.37, size * 0.87)
    lapel.closeSubpath()
    p.drawPath(lapel)

    p.setBrush(sash)
    p.drawRoundedRect(QRectF(size * 0.33, size * 0.70, size * 0.34, size * 0.06), 5, 5)

    belt_knot = QPainterPath()
    belt_knot.moveTo(size * 0.48, size * 0.72)
    belt_knot.quadTo(size * 0.45, size * 0.75, size * 0.48, size * 0.78)
    belt_knot.quadTo(size * 0.50, size * 0.75, size * 0.52, size * 0.78)
    belt_knot.quadTo(size * 0.55, size * 0.75, size * 0.52, size * 0.72)
    belt_knot.quadTo(size * 0.50, size * 0.75, size * 0.48, size * 0.72)
    p.setPen(QPen(QColor("#d5a4a7"), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(belt_knot)

    p.setPen(QPen(QColor("#d5a4a7"), 2))
    p.drawLine(int(size * 0.50), int(size * 0.75), int(size * 0.50), int(size * 0.86))
    p.drawLine(int(size * 0.50), int(size * 0.82), int(size * 0.47), int(size * 0.88))
    p.drawLine(int(size * 0.50), int(size * 0.82), int(size * 0.53), int(size * 0.90))
    p.restore()


def _draw_head(p: QPainter, size: int, skin: QColor, outline: QColor) -> None:
    p.save()
    p.setPen(QPen(outline, 3))
    p.setBrush(skin)
    p.drawEllipse(QRectF(size * 0.25, size * 0.17, size * 0.50, size * 0.38))
    p.restore()


def _draw_front_hair(p: QPainter, size: int, hair: QColor, outline: QColor, crown: QColor) -> None:
    p.save()
    p.setPen(QPen(outline, 3))
    p.setBrush(hair)

    cap = QPainterPath()
    cap.moveTo(size * 0.26, size * 0.31)
    cap.quadTo(size * 0.50, size * 0.08, size * 0.74, size * 0.32)
    cap.lineTo(size * 0.69, size * 0.47)
    cap.quadTo(size * 0.50, size * 0.29, size * 0.31, size * 0.47)
    cap.closeSubpath()
    p.drawPath(cap)

    bang_mid = QPainterPath()
    bang_mid.moveTo(size * 0.51, size * 0.18)
    bang_mid.quadTo(size * 0.46, size * 0.37, size * 0.38, size * 0.49)
    bang_mid.quadTo(size * 0.50, size * 0.46, size * 0.58, size * 0.32)
    bang_mid.closeSubpath()
    p.drawPath(bang_mid)

    bang_left = QPainterPath()
    bang_left.moveTo(size * 0.42, size * 0.22)
    bang_left.quadTo(size * 0.32, size * 0.30, size * 0.34, size * 0.44)
    bang_left.quadTo(size * 0.42, size * 0.41, size * 0.47, size * 0.28)
    bang_left.closeSubpath()
    p.drawPath(bang_left)

    bang_side = QPainterPath()
    bang_side.moveTo(size * 0.57, size * 0.20)
    bang_side.quadTo(size * 0.69, size * 0.30, size * 0.65, size * 0.49)
    bang_side.quadTo(size * 0.58, size * 0.45, size * 0.54, size * 0.26)
    bang_side.closeSubpath()
    p.drawPath(bang_side)

    p.setBrush(crown)
    p.drawRoundedRect(QRectF(size * 0.44, size * 0.04, size * 0.12, size * 0.15), 4, 4)
    p.drawRect(QRectF(size * 0.47, size * 0.00, size * 0.06, size * 0.05))
    p.restore()


def _draw_face(p: QPainter, size: int, mood: str, blush: QColor, outline: QColor) -> None:
    p.save()
    face_rect = QRectF(size * 0.25, size * 0.17, size * 0.50, size * 0.38)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(blush)
    p.drawEllipse(QPointF(face_rect.left() + size * 0.13, face_rect.center().y() + size * 0.06), 12, 9)
    p.drawEllipse(QPointF(face_rect.right() - size * 0.13, face_rect.center().y() + size * 0.06), 12, 9)

    p.setPen(QPen(outline, 3))
    eye_y = face_rect.center().y() + 3
    left_eye = QPointF(face_rect.left() + size * 0.13, eye_y)
    right_eye = QPointF(face_rect.right() - size * 0.13, eye_y)

    if mood in {"sleep", "blink", "peek"}:
        p.drawArc(int(left_eye.x() - 8), int(left_eye.y() - 1), 14, 10, 0, 180 * 16)
        p.drawArc(int(right_eye.x() - 8), int(right_eye.y() - 1), 14, 10, 0, 180 * 16)
    else:
        p.drawArc(int(left_eye.x() - 8), int(left_eye.y() - 2), 14, 11, 0, 180 * 16)
        p.drawArc(int(right_eye.x() - 8), int(right_eye.y() - 2), 14, 11, 0, 180 * 16)

    mouth = QPainterPath()
    mouth_y = face_rect.bottom() - size * 0.075
    if mood == "react":
        mouth.addEllipse(QRectF(face_rect.center().x() - 4, mouth_y - 5, 8, 10))
    elif mood == "peek":
        mouth.moveTo(face_rect.center().x() - 4, mouth_y)
        mouth.lineTo(face_rect.center().x() + 4, mouth_y)
    else:
        mouth.moveTo(face_rect.center().x() - 6, mouth_y)
        mouth.quadTo(face_rect.center().x(), mouth_y + 5, face_rect.center().x() + 6, mouth_y)
    p.drawPath(mouth)
    p.restore()


def _draw_feet(p: QPainter, size: int, outline: QColor) -> None:
    p.save()
    p.setPen(QPen(outline, 2))
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(size * 0.39, size * 0.90, size * 0.07, size * 0.045), 4, 4)
    p.drawRoundedRect(QRectF(size * 0.54, size * 0.90, size * 0.07, size * 0.045), 4, 4)
    p.restore()
