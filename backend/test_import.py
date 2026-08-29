import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    print("SUCCESS: Successfully imported app.main:app without errors!")
except Exception as e:
    import traceback
    print(f"IMPORT ERROR: {e}")
    traceback.print_exc()
