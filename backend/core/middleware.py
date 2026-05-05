from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class DevCorsMiddleware:
    """
    Minimal CORS middleware for local development.

    This repo runs the frontend on a different origin (Vite, e.g. :5190) than
    the Django API (:8000). Without CORS headers, browsers will block responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        origin = request.headers.get("Origin")
        allowed: Iterable[str] = getattr(settings, "DEV_CORS_ALLOWED_ORIGINS", ())

        # Handle preflight early.
        if request.method == "OPTIONS" and origin and origin in allowed:
            resp = HttpResponse(status=204)
            self._apply_headers(resp, origin)
            return resp

        resp = self.get_response(request)
        if origin and origin in allowed:
            self._apply_headers(resp, origin)
        return resp

    def _apply_headers(self, resp: HttpResponse, origin: str) -> None:
        resp["Access-Control-Allow-Origin"] = origin
        resp["Vary"] = "Origin"
        resp["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
        resp["Access-Control-Allow-Headers"] = "Authorization,Content-Type"

