# ---- Stage 1: Build ----
FROM python:3.12-slim AS build

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /build/dist

# ---- Stage 2: Production runtime ----
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/Faerkeren/GraphRender"

RUN groupadd -r graphrender && useradd -r -g graphrender -d /app graphrender

WORKDIR /app

# Install only the production wheel — no build tools in the final image
COPY --from=build /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -f /tmp/*.whl

# Copy themes for optional runtime use
COPY themes/ /app/themes/

# HTTP server port (configurable via GRAPHRENDER_PORT at runtime)
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

USER graphrender

CMD ["python", "-m", "graphrender.server"]
