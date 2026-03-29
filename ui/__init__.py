"""
Power Plant Simulator UI package.

Provides graphical user interface for building and simulating power plant diagrams.

Usage:
    from ui import run_app
    run_app()
"""

from .main_window import MainWindow, run_app

__all__ = [
    "MainWindow",
    "run_app",
]
