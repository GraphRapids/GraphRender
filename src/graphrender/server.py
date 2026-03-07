"""Lightweight HTTP server for GraphRender with health-check endpoint.

Endpoints
---------
GET  /health  -> {"status": "ok"} (200)
POST /render  -> SVG output from ELK JSON body

Run directly::

    python -m graphrender.server

Configuration via environment variables:

- ``GRAPHRENDER_PORT`` – listen port (default ``8080``)
"""

from __future__ import annotations

import json
import logging
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

#: Maximum accepted request body size (10 MB).
MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024


class _Handler(BaseHTTPRequestHandler):
    """HTTP request handler for the GraphRender server."""

    server_version = "GraphRender/1.0"

    # -- routing --------------------------------------------------------- #

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._respond_json(HTTPStatus.OK, {"status": "ok"})
        else:
            self._respond_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/render":
            self._handle_render()
        else:
            self._respond_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    # -- /render --------------------------------------------------------- #

    def _handle_render(self) -> None:
        content_length_hdr = self.headers.get("Content-Length")
        if content_length_hdr is None:
            self._respond_json(
                HTTPStatus.LENGTH_REQUIRED,
                {"error": "Content-Length required"},
            )
            return

        try:
            content_length = int(content_length_hdr)
        except (ValueError, OverflowError):
            self._respond_json(
                HTTPStatus.BAD_REQUEST, {"error": "invalid Content-Length"}
            )
            return

        if content_length < 0 or content_length > MAX_CONTENT_LENGTH:
            self._respond_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "payload too large"},
            )
            return

        try:
            body = self.rfile.read(content_length)
            graph = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._respond_json(
                HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"}
            )
            return

        try:
            # Lazy import keeps /health fast and avoids circular imports.
            from graphrender import GraphRender  # noqa: WPS433

            renderer = GraphRender(graph=graph)
            svg_text = renderer.to_string()
        except Exception:
            logger.exception("Render failed")
            # Never leak internal details to the client.
            self._respond_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal server error"},
            )
            return

        encoded = svg_text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    # -- helpers --------------------------------------------------------- #

    def _respond_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        logger.info(format, *args)


def run(host: str = "0.0.0.0", port: int | None = None) -> None:
    """Start the GraphRender HTTP server."""
    if port is None:
        port = int(os.environ.get("GRAPHRENDER_PORT", "8080"))
    server = HTTPServer((host, port), _Handler)
    logger.info("GraphRender server listening on %s:%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    run()
