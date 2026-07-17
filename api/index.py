import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

# Tambahkan backend ke path agar import file lokal (cv_analyzer, dll) jalan di Vercel
sys.path.insert(0, backend_dir)
sys.path.insert(0, root_dir)

# Set working directory
os.chdir(backend_dir)

from backend.main import app
