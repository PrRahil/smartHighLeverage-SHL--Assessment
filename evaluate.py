"""
Evaluate script runner - generates submission CSV
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.evaluate import main

if __name__ == "__main__":
    sys.exit(main())