from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from desktop_pet.config import PetSettings


class SettingsDialog(QDialog):
    settings_changed = Signal(PetSettings)

    def __init__(self, settings: PetSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("桌宠设置")
        self.setModal(False)
        self.setMinimumWidth(360)
        self._settings = settings

        self.scale_slider = self._slider(70, 180, int(settings.scale * 100))
        self.speed_slider = self._slider(1, 12, settings.speed)
        self.activity_slider = self._slider(800, 5000, settings.activity_interval_ms)

        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems(["quiet", "normal", "active"])
        self.behavior_combo.setCurrentText(settings.behavior_mode)

        self.click_checkbox = QCheckBox("鼠标穿透")
        self.click_checkbox.setChecked(settings.click_through)
        self.top_checkbox = QCheckBox("始终置顶")
        self.top_checkbox.setChecked(settings.always_on_top)
        self.fullscreen_checkbox = QCheckBox("全屏时自动隐藏")
        self.fullscreen_checkbox.setChecked(settings.auto_hide_fullscreen)

        form = QFormLayout()
        form.addRow("缩放", self._with_value(self.scale_slider, lambda: f"{self.scale_slider.value()}%"))
        form.addRow("速度", self._with_value(self.speed_slider, lambda: str(self.speed_slider.value())))
        form.addRow(
            "动作间隔",
            self._with_value(self.activity_slider, lambda: f"{self.activity_slider.value()} ms"),
        )
        form.addRow("活跃度", self.behavior_combo)
        form.addRow("", self.click_checkbox)
        form.addRow("", self.top_checkbox)
        form.addRow("", self.fullscreen_checkbox)

        buttons = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._emit_settings)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.hide)
        buttons.addStretch(1)
        buttons.addWidget(save_button)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _slider(self, minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        return slider

    def _with_value(self, widget: QSlider, formatter) -> QHBoxLayout:
        label = QLabel(formatter())
        widget.valueChanged.connect(lambda _: label.setText(formatter()))
        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(label)
        return layout

    def _emit_settings(self) -> None:
        new_settings = PetSettings(
            scale=self.scale_slider.value() / 100,
            speed=self.speed_slider.value(),
            activity_interval_ms=self.activity_slider.value(),
            click_through=self.click_checkbox.isChecked(),
            always_on_top=self.top_checkbox.isChecked(),
            muted=self._settings.muted,
            auto_hide_fullscreen=self.fullscreen_checkbox.isChecked(),
            behavior_mode=self.behavior_combo.currentText(),
            edge=self._settings.edge,
            offset=self._settings.offset,
        )
        self.settings_changed.emit(new_settings)
