from app import app
import os

if __name__ == "__main__":
    # PUBLIC_INTERFACE
    # Entrypoint to run the Flask development server.
    # Binds to 0.0.0.0 and port 3001 by default so the service is reachable by the frontend.
    # You can override with HOST and PORT environment variables (or FLASK_RUN_PORT).
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("FLASK_RUN_PORT", "3001")))
    debug = os.environ.get("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(host=host, port=port, debug=debug, threaded=True)
