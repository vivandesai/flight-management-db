"""Local entrypoint: one Python server, no frontend build."""
import os
from waitress import serve
from airline import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "5000"))
    print(f"Airline management: http://127.0.0.1:{port}", flush=True)
    serve(app, host="127.0.0.1", port=port)
