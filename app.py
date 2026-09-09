"""Application entry point for WSGI / ASGI servers and local development."""

import os
from app import create_app
from app.config import get_config

config = get_config()
app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    # In development, use Waitress if available or Flask built-in server with debug=False for safety
    print(f"🚀 AI News Intelligence Platform running on http://{host}:{port}")
    app.run(host=host, port=port, debug=config.DEBUG)
