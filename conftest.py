"""Configuracion de pytest - agrega src/ al path para imports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
