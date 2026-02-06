import sys
import os

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from .nodes import NODE_CLASS_MAPPINGS

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY", "start_backend_server"]

_backend_server = None


def start_backend_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn

    global _backend_server

    if _backend_server is None:
        import threading

        print("=" * 60)
        print("🚀 Starting ComfyUI Workflow Agent Backend Server")
        print("=" * 60)
        print(f"📡 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"📚 API Documentation: http://{host}:{port}/docs")
        print(f"📖 ReDoc: http://{host}:{port}/redoc")
        print("=" * 60)

        def run_server():
            print(f"\n✅ Backend server is running on http://{host}:{port}")
            print(f"⏰ Started at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"💡 Press Ctrl+C to stop the server\n")

            try:
                from backend.main import app
                uvicorn.run(app, host=host, port=port, log_level="info")
            except Exception as e:
                print(f"❌ Error loading backend module: {e}")
                import traceback
                traceback.print_exc()
                raise

        _backend_server = threading.Thread(target=run_server, daemon=True)
        _backend_server.start()

        print(f"🔄 Backend server thread started in background")
        print("=" * 60)
    else:
        print("⚠️  Backend server is already running!")

    return _backend_server


_start_backend_server = start_backend_server

import threading
import atexit


def _auto_start_backend():
    try:
        start_backend_server(host="127.0.0.1", port=8000)
    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")


def _cleanup():
    global _backend_server
    if _backend_server is not None:
        print("🛑 Shutting down backend server...")


_thread = threading.Thread(target=_auto_start_backend, daemon=True)
_thread.start()

atexit.register(_cleanup)
