from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop_pet.config import load_settings
from desktop_pet.pet_window import PetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Pet")
    app.setQuitOnLastWindowClosed(False)

    settings = load_settings()
    pet = PetWindow(settings)
    pet.show()

    return app.exec()
