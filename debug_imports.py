"""Debug why audio and renders routers fail to import."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

# Set env to avoid missing .env issues
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./storyforge.db")

try:
    from app.api import audio
    print("audio router: OK")
except Exception as e:
    print(f"audio router FAIL: {type(e).__name__}: {e}")

try:
    from app.api import renders
    print("renders router: OK")
except Exception as e:
    print(f"renders router FAIL: {type(e).__name__}: {e}")
