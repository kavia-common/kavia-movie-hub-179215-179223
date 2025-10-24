import json
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
    photo_url = fields.Str(allow_none=True, description="Poster image URL for the movie")
    created_at = fields.DateTime(dump_only=True, allow_none=True, description="Creation timestamp")


class MovieCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1), description="Title of the movie")
    year = fields.Int(allow_none=True, description="Release year of the movie")
    overview = fields.Str(allow_none=True, description="Short description of the movie")
    photo_url = fields.Str(allow_none=True, description="Poster image URL for the movie")


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

        Each movie includes its id, title, year, overview, created_at, and photo_url (if provided).

        Returns:
            200: JSON array of movie records.
            500: JSON error if configuration or database fetch fails.
        """
        current_app.logger.info(json.dumps({"event": "movies_get_start"}))
        try:
            supabase = get_supabase()
        except RuntimeError as e:
            current_app.logger.error(json.dumps({
                "event": "movies_get_supabase_init_error",
                "message": str(e)
            }))
            blp.abort(500, message=str(e))

        try:
            # Use '*' to avoid errors if optional columns (e.g., photo_url) are absent
            res = supabase.table("movies").select("*").execute()
            data = getattr(res, "data", None)
            if data is None:
                data = []
            current_app.logger.info(json.dumps({
                "event": "movies_get_success",
                "count": len(data)
            }))
            return data
        except Exception as exc:
            current_app.logger.exception("Failed to fetch movies from Supabase")
            current_app.logger.error(json.dumps({
                "event": "movies_get_failure",
                "message": str(exc)
            }))
            blp.abort(500, message="Failed to fetch movies")

    # PUBLIC_INTERFACE
    @blp.arguments(
        MovieCreateSchema,
        example={
            "title": "Inception",
            "year": 2010,
            "overview": "A mind-bending heist.",
            "photo_url": "https://image.tmdb.org/t/p/w500/example.jpg",
        },
    )
    @blp.response(201, MovieSchema, description="Create a new movie")
    def post(self, new_movie):
        """Create a new movie record in the 'movies' table.

        Request JSON:
            - title (string, required)
            - year (integer, optional)
            - overview (string, optional)
            - photo_url (string, optional) - Poster image URL for the movie

        Returns:
            201: The newly created movie record as JSON.
            400: If validation fails.
            422: If JSON body validation fails (marshmallow).
            500: If configuration or database operation fails.
        """
        # Title is required; safeguard beyond schema
        title = (new_movie.get("title") or "").strip()
        if not title:
            current_app.logger.warning(json.dumps({
                "event": "movies_post_validation_error",
                "message": "title is empty after trimming"
            }))
            blp.abort(400, message="Field 'title' is required and cannot be empty.")

        # photo_url is optional; if provided, ensure it's a string (marshmallow already deserializes to str)
        # Keeping an explicit check for clarity and to align with the requirement.
        photo_url = new_movie.get("photo_url", None)
        if photo_url is not None and not isinstance(photo_url, str):
            current_app.logger.warning(json.dumps({
                "event": "movies_post_validation_error",
                "message": "photo_url must be a string when provided"
            }))
            blp.abort(400, message="Field 'photo_url' must be a string if provided.")

        # Log attempt with minimal context (no secret values)
        current_app.logger.info(json.dumps({
            "event": "movies_post_start",
            "payload_keys": sorted(list(new_movie.keys()))
        }))

        try:
            supabase = get_supabase()
        except RuntimeError as e:
            current_app.logger.error(json.dumps({
                "event": "movies_post_supabase_init_error",
                "message": str(e)
            }))
            blp.abort(500, message=str(e))

        def _insert(payload: dict):
            res_local = supabase.table("movies").insert(payload).execute()
            data_local = getattr(res_local, "data", None)
            if not data_local:
                current_app.logger.error(json.dumps({
                    "event": "movies_post_insert_no_data"
                }))
                blp.abort(500, message="Insert failed: no data returned from Supabase")
            return data_local[0]

        # First attempt
        try:
            created = _insert(new_movie)
            current_app.logger.info(json.dumps({
                "event": "movies_post_success",
                "id": created.get("id")
            }))
            return created
        except Exception as exc:
            # On error, if photo_url was provided, attempt to retry without it
            err_text = str(exc)
            current_app.logger.exception("Failed to insert movie into Supabase")
            current_app.logger.warning(json.dumps({
                "event": "movies_post_insert_error",
                "message": err_text,
                "had_photo_url": "photo_url" in new_movie
            }))

            if "photo_url" in new_movie and (
                "column" in err_text.lower()
                or "unknown" in err_text.lower()
                or "invalid input" in err_text.lower()
                or "does not exist" in err_text.lower()
                or "undefined" in err_text.lower()
            ):
                # Retry without photo_url in case the column is not present in the DB
                safe_payload = {k: v for k, v in new_movie.items() if k != "photo_url"}
                try:
                    created = _insert(safe_payload)
                    current_app.logger.info(json.dumps({
                        "event": "movies_post_success_without_photo_url",
                        "id": created.get("id")
                    }))
                    return created
                except Exception:
                    current_app.logger.exception("Retry insert without photo_url failed")
                    blp.abort(500, message="Failed to create movie")
            else:
                blp.abort(500, message="Failed to create movie")
