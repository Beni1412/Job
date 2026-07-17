import sys
import os

# Tambahkan root project ke path agar backend bisa di-import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
