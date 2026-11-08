"""Run the Trading Data chatbot UI."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import ui.bootstrap  # noqa: F401

from chatbot.app import main

if __name__ == "__main__":
    main()
