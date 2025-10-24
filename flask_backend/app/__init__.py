import os
import logging
import json
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

# Import blueprints
from .routes.health import blp as health_blp
from .routes.hello import blp as hello_blp
from .routes.movies import blp as movies_blp

# Simple JSON formatter for structured logs (no external dependencies)
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        # Add location
        payload["pathname"] = record.pathname
        payload["lineno"] = record.lineno
        # Include exception text when present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Attach extra dict-like attributes if provided via LoggerAdapter or extra
        for key in ("event", "context", "request_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configure structured JSON logging
log_level = os.getenv("FLASK_LOG_LEVEL", "INFO").upper()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
# Configure app logger
app.logger.handlers.clear()
app.logger.addHandler(handler)
app.logger.setLevel(log_level)
# Also set root logger for any library logs
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.addHandler(handler)
root_logger.setLevel(log_level)

# Log Supabase env presence (do not log secrets)
has_supabase_url = bool(os.getenv("SUPABASE_URL"))
has_supabase_service_key = bool(os.getenv("SUPABASE_SERVICE_KEY"))
app.logger.info(
    json.dumps({
        "event": "startup",
        "component": "flask_app",
        "supabase_env": {"has_url": has_supabase_url, "has_service_key": has_supabase_service_key},
    })
)

# Configure CORS to allow React dev server, preview origin, and optional deployed FRONTEND_URL
# - Credentials remain disabled (default False)
# - Preflight (OPTIONS) will be handled by flask-cors automatically
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vscode-internal-30361-beta.beta01.cloud.kavia.ai:3000",
    "https://kavia-bootcamp-movie-application.kavia.app/"
]

CORS(
    app,
    resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": False,
        }
    },
)

# OpenAPI/Docs configuration
app.config["API_TITLE"] = "My Flask API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

# Register blueprints
api.register_blueprint(health_blp)
api.register_blueprint(hello_blp)
api.register_blueprint(movies_blp)
