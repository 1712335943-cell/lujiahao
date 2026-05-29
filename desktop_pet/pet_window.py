from __future__ import annotations

import math
import random
from typing import Optional

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QAction, QCursor, QIcon, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)

from desktop_pet.assets import PetSpriteStore
from desktop_pet.config import PetSettings, save_settings
from desktop_pet.settings_window import SettingsDialog
from desktop_pet.state import PetState


class PetWindow(QWidget):
    def __init__(self, settings: PetSettings) -> None:
        super().__init__(None)
        self.settings = settings
        self.state = PetState(edge=settings.edge, offset=settings.offset)
        self.blink = False
        self._drag_pos: Optional[QPoint] = None
        self._press_pos: Optional[QPoint] = None
        self._drag_started = False
        self._animation_tick = 0
        self._cute_action: Optional[str] = None
        self._cute_action_tick = 0
        self._cute_action_duration = 0

        self.sprite_store = PetSpriteStore(settings.scale)
        self.pet_width, self.pet_height = self.sprite_store.frame_size()
        self._apply_window_flags()
        self.resize(self.pet_width, self.pet_height)
        self._create_message_bubble()

        self.settings_dialog = SettingsDialog(settings)
        self.settings_dialog.settings_changed.connect(self.update_settings)

        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.advance_along_edge)
        self.move_timer.start(42)

        self.mood_timer = QTimer(self)
        self.mood_timer.timeout.connect(self.randomize_mood)
        self.mood_timer.start(self.settings.activity_interval_ms)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(1100)

        self.interaction_timer = QTimer(self)
        self.interaction_timer.setSingleShot(True)
        self.interaction_timer.timeout.connect(self.reset_interaction)

        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.message_bubble.hide)

        self.cute_action_timer = QTimer(self)
        self.cute_action_timer.timeout.connect(self.start_random_cute_action)
        self._schedule_next_cute_action()

        self._create_tray()
        self.snap_to_edge(self.state.edge, self.state.offset)
        self.show()

    def _apply_window_flags(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        if self.settings.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.set_click_through(self.settings.click_through)

    def _create_tray(self) -> None:
        self.tray = QSystemTrayIcon(QIcon(self._current_pixmap()), self)
        menu = QMenu()

        self.pause_action = QAction("暂停巡逻", self)
        self.pause_action.triggered.connect(self.toggle_pause)
        menu.addAction(self.pause_action)

        menu.addAction("逗一下", self.trigger_interaction)
        menu.addAction("设置", self.settings_dialog.show)
        menu.addAction("回到右边", lambda: self.snap_to_edge("right", 180))
        menu.addAction("回到底边", lambda: self.snap_to_edge("bottom", 280))
        menu.addAction("显示/隐藏", self.toggle_visibility)
        menu.addSeparator()
        menu.addAction("退出", QApplication.instance().quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._handle_tray_click)
        self.tray.show()

    def _handle_tray_click(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def _current_pixmap(self):
        mood = "blink" if self.blink and self.state.mood not in {"react", "sleep"} else self.state.mood
        return self.sprite_store.pixmap(mood, self.state.edge, self.state.direction)

    def _create_message_bubble(self) -> None:
        self.message_bubble = QLabel("", None)
        self.message_bubble.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.message_bubble.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.message_bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_bubble.setWordWrap(True)
        self.message_bubble.setStyleSheet(
            """
            QLabel {
                background-color: rgba(28, 30, 34, 232);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 13px;
            }
            """
        )

    def _position_message_bubble(self) -> None:
        if not self.message_bubble.isVisible():
            return

        self.message_bubble.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        width = min(self.message_bubble.width(), 220)
        height = self.message_bubble.height()
        margin = 8

        if self.state.edge == "bottom":
            x = self.x() + (self.width() - width) // 2
            y = self.y() - height - margin
        elif self.state.edge == "top":
            x = self.x() + (self.width() - width) // 2
            y = self.y() + self.height() + margin
        elif self.state.edge == "left":
            x = self.x() + self.width() + margin
            y = self.y() + (self.height() - height) // 2
        else:
            x = self.x() - width - margin
            y = self.y() + (self.height() - height) // 2

        x = max(screen.left(), min(x, screen.right() - width))
        y = max(screen.top(), min(y, screen.bottom() - height))
        self.message_bubble.resize(width, height)
        self.message_bubble.move(x, y)

    def paintEvent(self, event: QPaintEvent) -> None:
        pixmap = self._current_pixmap()
        dx, dy, scale, rotation = self._animation_pose()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.translate(self.width() / 2 + dx, self.height() / 2 + dy)
        painter.rotate(rotation)
        painter.scale(scale, scale)
        painter.drawPixmap(-pixmap.width() // 2, -pixmap.height() // 2, pixmap)
        painter.end()

    def _animation_pose(self) -> tuple[float, float, float, float]:
        inward_x, inward_y = self._edge_inward_vector()
        tangent_x, tangent_y = self._edge_tangent_vector()
        phase = self._animation_tick * 0.16
        breath = math.sin(phase) * 1.15

        dx = inward_x * breath
        dy = inward_y * breath
        scale = 1 + math.sin(phase + 0.8) * 0.01
        rotation = math.sin(self._animation_tick * 0.075) * 0.55

        if self.message_bubble.isVisible() and not self.state.dragging:
            talk_phase = self._animation_tick * 0.75
            nod = abs(math.sin(talk_phase)) * 2.6
            sway = math.sin(talk_phase * 0.72) * 1.4
            dx += inward_x * nod + tangent_x * sway
            dy += inward_y * nod + tangent_y * sway
            scale += math.sin(talk_phase * 1.15) * 0.012
            rotation += math.sin(talk_phase * 0.9) * 1.8

        if self._cute_action and self._cute_action_duration > 0:
            progress = min(1, self._cute_action_tick / self._cute_action_duration)
            ease = math.sin(progress * math.pi)
            decay = 1 - progress

            if self._cute_action == "hop":
                jump = ease * 5.5
                dx += inward_x * jump
                dy += inward_y * jump
                scale += ease * 0.018
            elif self._cute_action == "wiggle":
                rotation += math.sin(progress * math.pi * 6) * 5.5 * decay
                dx += tangent_x * math.sin(progress * math.pi * 4) * 2.2 * decay
                dy += tangent_y * math.sin(progress * math.pi * 4) * 2.2 * decay
            elif self._cute_action == "squish":
                scale += ease * 0.026
                dx += inward_x * ease * 2.4
                dy += inward_y * ease * 2.4
            elif self._cute_action == "bounce":
                bounce = abs(math.sin(progress * math.pi * 2)) * 4.8 * decay
                dx += inward_x * bounce
                dy += inward_y * bounce
                scale += abs(math.sin(progress * math.pi * 2)) * 0.018 * decay
            elif self._cute_action == "peek":
                peek = math.sin(progress * math.pi) * 5.0
                dx += inward_x * peek + tangent_x * math.sin(progress * math.pi * 2) * 1.4
                dy += inward_y * peek + tangent_y * math.sin(progress * math.pi * 2) * 1.4
                rotation += math.sin(progress * math.pi * 2) * 2.2 * decay
            elif self._cute_action == "turn":
                rotation += math.sin(progress * math.pi) * 11.0
                scale += ease * 0.012
            elif self._cute_action == "shake":
                rotation += math.sin(progress * math.pi * 9) * 4.2 * decay
                dx += tangent_x * math.sin(progress * math.pi * 9) * 1.8 * decay
                dy += tangent_y * math.sin(progress * math.pi * 9) * 1.8 * decay

        return dx, dy, scale, rotation

    def _edge_inward_vector(self) -> tuple[int, int]:
        if self.state.edge == "top":
            return 0, 1
        if self.state.edge == "bottom":
            return 0, -1
        if self.state.edge == "left":
            return 1, 0
        return -1, 0

    def _edge_tangent_vector(self) -> tuple[int, int]:
        if self.state.edge in {"top", "bottom"}:
            return self.state.direction or 1, 0
        return 0, self.state.direction or 1

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.state.dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = event.globalPosition().toPoint()
            self._drag_started = False
            self.state.mood = "react"
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.tray.contextMenu().popup(QCursor.pos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.state.dragging and self._drag_pos is not None:
            if self._press_pos is not None:
                distance = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
                self._drag_started = self._drag_started or distance > 8
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._position_message_bubble()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            was_click = not self._drag_started
            self.state.dragging = False
            self._drag_pos = None
            self._press_pos = None
            if was_click:
                self.react_to_click()
            else:
                edge, offset = self._nearest_edge_and_offset()
                self.snap_to_edge(edge, offset)
                self.state.mood = "idle"
                self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.settings_dialog.show()

    def toggle_pause(self) -> None:
        self.state.paused = not self.state.paused
        self.pause_action.setText("继续巡逻" if self.state.paused else "暂停巡逻")
        self.state.mood = "sleep" if self.state.paused else "idle"
        self.message_bubble.hide()
        self.update()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def set_click_through(self, enabled: bool) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

    def update_settings(self, settings: PetSettings) -> None:
        self.settings = settings
        self.sprite_store = PetSpriteStore(settings.scale)
        self.pet_width, self.pet_height = self.sprite_store.frame_size()
        self.resize(self.pet_width, self.pet_height)
        self.mood_timer.start(self.settings.activity_interval_ms)
        self._apply_window_flags()
        self.show()
        self.snap_to_edge(self.state.edge, self.state.offset)
        settings.edge = self.state.edge
        settings.offset = self.state.offset
        save_settings(settings)
        self.update()

    def trigger_interaction(self) -> None:
        self.state.mood = "react"
        self.message_bubble.hide()
        self.start_cute_action(random.choice(("hop", "wiggle", "squish", "bounce", "peek", "turn", "shake")))
        self.interaction_timer.start(1300)
        self.update()

    def react_to_click(self) -> None:
        self.state.mood = "react"
        self.message_bubble.hide()
        self.start_cute_action(random.choice(("wiggle", "bounce", "peek", "shake")))
        self.interaction_timer.start(1200)
        self.update()

    def reset_interaction(self) -> None:
        if self.state.dragging or self.state.paused:
            return
        self.state.mood = "idle"
        self.update()

    def randomize_mood(self) -> None:
        if self.state.paused or self.state.dragging:
            return
        mode = self.settings.behavior_mode
        choices = {
            "quiet": ["idle", "idle", "peek", "sleep"],
            "normal": ["idle", "peek", "idle", "react"],
            "active": ["idle", "peek", "react", "idle", "corner"],
        }.get(mode, ["idle", "peek", "react"])
        self.state.mood = random.choice(choices)
        self.update()

    def toggle_blink(self) -> None:
        self.blink = not self.blink
        self.update()

    def advance_along_edge(self) -> None:
        self._advance_animation()
        if self.state.paused or self.state.dragging:
            return

        screen = self.screen().availableGeometry() if self.screen() else QApplication.primaryScreen().availableGeometry()
        step = self.settings.speed
        max_offset = self._max_offset_for_edge(self.state.edge, screen)

        self.state.offset += step * self.state.direction
        self.state.move_tick += 1

        if self.state.offset >= max_offset:
            self.state.offset = max_offset
            self.turn_corner()
        elif self.state.offset <= 0:
            self.state.offset = 0
            self.turn_corner()

        self.snap_to_edge(self.state.edge, self.state.offset, persist=False)
        self._position_message_bubble()

        if self.state.move_tick % 70 == 0 and self.state.mood not in {"peek", "react"}:
            self.state.mood = "idle"

    def turn_corner(self) -> None:
        self.state.mood = "corner"
        self.state.edge, self.state.offset, self.state.direction = self._next_edge_from_corner(
            self.state.edge,
            self.state.offset,
        )
        self.start_cute_action("hop")
        self.update()

    def _advance_animation(self) -> None:
        self._animation_tick += 1
        if self._cute_action:
            self._cute_action_tick += 1
            if self._cute_action_tick >= self._cute_action_duration:
                self._cute_action = None
                self._cute_action_tick = 0
                self._cute_action_duration = 0
        self.update()

    def start_cute_action(self, action: str) -> None:
        durations = {
            "hop": 16,
            "wiggle": 18,
            "squish": 14,
            "bounce": 24,
            "peek": 22,
            "turn": 20,
            "shake": 16,
        }
        self._cute_action = action
        self._cute_action_tick = 0
        self._cute_action_duration = durations.get(action, 14)

    def start_random_cute_action(self) -> None:
        if not self.state.paused and not self.state.dragging and self.isVisible():
            self.start_cute_action(random.choice(("hop", "wiggle", "squish", "bounce", "peek", "turn", "shake")))
        self._schedule_next_cute_action()

    def _schedule_next_cute_action(self) -> None:
        self.cute_action_timer.start(random.randint(4_000, 8_000))

    def _max_offset_for_edge(self, edge: str, screen=None) -> int:
        screen = screen or QApplication.primaryScreen().availableGeometry()
        if edge in {"top", "bottom"}:
            return max(0, screen.width() - self.pet_width)
        return max(0, screen.height() - self.pet_height)

    def _next_edge_from_corner(self, edge: str, offset: int) -> tuple[str, int, int]:
        bottom_max = self._max_offset_for_edge("bottom")
        left_max = self._max_offset_for_edge("left")
        right_max = self._max_offset_for_edge("right")

        if edge == "bottom" and offset <= 0:
            return random.choice((("left", left_max, -1), ("bottom", 0, 1)))
        if edge == "bottom" and offset >= bottom_max:
            return random.choice((("right", right_max, -1), ("bottom", bottom_max, -1)))
        if edge == "left" and offset <= 0:
            return "left", 0, 1
        if edge == "left" and offset >= left_max:
            return random.choice((("bottom", 0, 1), ("left", left_max, -1)))
        if edge == "right" and offset <= 0:
            return "right", 0, 1
        if edge == "right" and offset >= right_max:
            return random.choice((("bottom", bottom_max, -1), ("right", right_max, -1)))
        if edge == "top":
            return "bottom", min(offset, bottom_max), random.choice((-1, 1))
        return edge, offset, self.state.direction

    def _direction_for_edge(self, edge: str) -> int:
        return self.state.direction if edge == self.state.edge else -1 if edge in {"bottom", "left"} else 1

    def snap_to_edge(self, edge: str, offset: int, persist: bool = True) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        offset = max(0, offset)
        side_visible_ratio = 0.72
        top_visible_ratio = 0.38
        bottom_visible_ratio = 0.58
        hidden_x = int(self.pet_width * (1 - side_visible_ratio))
        hidden_top_y = int(self.pet_height * (1 - top_visible_ratio))

        if edge == "top":
            offset = min(offset, screen.width() - self.pet_width)
            self.move(screen.left() + offset, screen.top() - hidden_top_y)
        elif edge == "bottom":
            offset = min(offset, screen.width() - self.pet_width)
            self.move(screen.left() + offset, screen.bottom() - int(self.pet_height * bottom_visible_ratio) + 1)
        elif edge == "left":
            offset = min(offset, screen.height() - self.pet_height)
            self.move(screen.left() - hidden_x, screen.top() + offset)
        else:
            edge = "right"
            offset = min(offset, screen.height() - self.pet_height)
            self.move(screen.right() - int(self.pet_width * side_visible_ratio) + 1, screen.top() + offset)

        self.state.edge = edge
        self.state.offset = int(offset)
        self.state.direction = self._direction_for_edge(edge)
        if persist:
            self.settings.edge = self.state.edge
            self.settings.offset = self.state.offset
            save_settings(self.settings)
        self._position_message_bubble()
        self.update()

    def _nearest_edge_and_offset(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()

        left_distance = abs(geo.left() - screen.left())
        right_distance = abs(screen.right() - geo.right())
        top_distance = abs(geo.top() - screen.top())
        bottom_distance = abs(screen.bottom() - geo.bottom())

        distances = {
            "left": left_distance,
            "right": right_distance,
            "bottom": bottom_distance,
        }
        edge = min(distances, key=distances.get)

        if edge in {"left", "right"}:
            offset = geo.top() - screen.top()
        else:
            offset = geo.left() - screen.left()
        return edge, max(0, int(offset))
