from flask_smorest import Blueprint
from flask.views import MethodView
from flask import Response

# Define blueprint for Hello endpoint
blp = Blueprint(
    "Hello",
    "hello",
    url_prefix="/api",
    description="Basic hello endpoint for connectivity checks",
)

@blp.route("/hello")
class HelloView(MethodView):
    # PUBLIC_INTERFACE
    def get(self):
        """Return a plain text greeting for connectivity test."""
        # Return plain text as per acceptance criteria
        return Response("Hello from Flask", mimetype="text/plain", status=200)
