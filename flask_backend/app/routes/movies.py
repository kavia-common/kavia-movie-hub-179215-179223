from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields, validate
from flask import current_app

from app.services.supabase_client import get_supabase


# Schemas for request/response validation and documentation
class MovieSchema(Schema):
    id = fields.Int(dump_only=True, description="Primary key identifier")
    title = fields.Str(required=True, description="Title of the movie")
    year = fields.Int(allow_none=True, description="Release year of the movie")
    overview = fields.Str(allow_none=True, description="Short description of the movie")
    created_at = fields.DateTime(dump_only=True, allow_none=True, description="Creation timestamp")


class MovieCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1), description="Title of the movie")
    year = fields.Int(allow_none=True, description="Release year of the movie")
    overview = fields.Str(allow_none=True, description="Short description of the movie")


# Define blueprint for Movies endpoints
blp = Blueprint(
    "Movies",
    "movies",
    url_prefix="/api",
    description="Endpoints to manage movies via Supabase",
)


@blp.route("/movies")
class MoviesList(MethodView):
    # PUBLIC_INTERFACE
    @blp.response(200, MovieSchema(many=True), description="List all movies")
    def get(self):
        """Fetch a list of movies from the 'movies' table in Supabase.

        Returns:
            200: JSON array of movie records.
            500: JSON error if configuration or database fetch fails.
        """
        try:
            supabase = get_supabase()
        except RuntimeError as e:
            blp.abort(500, message=str(e))

        try:
            res = supabase.table("movies").select("*").execute()
            data = getattr(res, "data", None)
            if data is None:
                # Fallback in case library version behaves differently
                data = []
            return data
        except Exception:
            current_app.logger.exception("Failed to fetch movies from Supabase")
            blp.abort(500, message="Failed to fetch movies")

    # PUBLIC_INTERFACE
    @blp.arguments(MovieCreateSchema, example={"title": "Inception", "year": 2010, "overview": "A mind-bending heist."})
    @blp.response(201, MovieSchema, description="Create a new movie")
    def post(self, new_movie):
        """Create a new movie record in the 'movies' table.

        Request JSON:
            - title (string, required)
            - year (integer, optional)
            - overview (string, optional)

        Returns:
            201: The newly created movie record as JSON.
            400: If validation fails.
            500: If configuration or database operation fails.
        """
        # Title is required; safeguard beyond schema
        title = (new_movie.get("title") or "").strip()
        if not title:
            blp.abort(400, message="Field 'title' is required and cannot be empty.")

        try:
            supabase = get_supabase()
        except RuntimeError as e:
            blp.abort(500, message=str(e))

        try:
            res = supabase.table("movies").insert(new_movie).execute()
            data = getattr(res, "data", None)
            if not data:
                blp.abort(500, message="Insert failed: no data returned from Supabase")
            # Return the first inserted row
            return data[0]
        except Exception:
            current_app.logger.exception("Failed to insert movie into Supabase")
            blp.abort(500, message="Failed to create movie")
