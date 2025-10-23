import os
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

# Import blueprints
from .routes.health import blp as health_blp
from .routes.hello import blp as hello_blp

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configure CORS to allow React dev server, preview origin, and optional deployed FRONTEND_URL
# - Credentials remain disabled (default False)
# - Preflight (OPTIONS) will be handled by flask-cors automatically
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://vscode-internal-33523-beta.beta01.cloud.kavia.ai:3000",
]

# Read FRONTEND_URL from environment and add it if provided (no trailing slash)
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    frontend_url = frontend_url.strip().rstrip("/")
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)

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
