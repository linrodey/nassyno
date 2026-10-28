FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then PIP_CERT=/run/secrets/build_ca python -m pip install --no-cache-dir -r requirements.txt; else python -m pip install --no-cache-dir -r requirements.txt; fi
COPY --chown=10001:10001 backend ./backend
COPY --chown=10001:10001 web ./web
USER 10001:10001
CMD ["python", "-m", "uvicorn", "backend.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
