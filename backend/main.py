import hmac
import asyncio
import ipaddress
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .auth_check import check_auth
from .config import Settings
from .dsm import DsmProbe, ProbeError

ROOT = Path(__file__).resolve().parents[1]

def create_app(settings=None, probe=None, auth_checker=None):
    settings = settings or Settings.from_env()
    probe = probe or DsmProbe()
    app = FastAPI(title='NAS Manager — connection foundation', docs_url=None, redoc_url=None, openapi_url=None)
    devices = {d.id:d for d in settings.devices}
    auth_checker = auth_checker or check_auth
    attempts = {}
    active = set()
    pending = set()

    @app.middleware('http')
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.url.scheme == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    def authorized(authorization: str | None = Header(default=None)):
        expected = 'Bearer '+settings.admin_token
        if authorization is None or not hmac.compare_digest(authorization.encode(), expected.encode()):
            raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate':'Bearer'})

    @app.get('/healthz')
    async def health():
        return {'status':'ok', 'stage':'connection-foundation', 'nas_readiness':'not_verified'}

    @app.get('/api/v1/devices', dependencies=[Depends(authorized)])
    async def inventory():
        return {'devices':[d.public() for d in settings.devices]}

    @app.post('/api/v1/devices/{device_id}/probe', dependencies=[Depends(authorized)])
    async def check(device_id: str):
        if device_id not in devices:
            raise HTTPException(404, 'Device not configured')
        try:
            result = await probe.probe(devices[device_id])
        except ProbeError as exc:
            return JSONResponse(status_code=502, content={'device_id':device_id, 'status':'failed', **exc.public()})
        result['observed_at'] = datetime.now(timezone.utc).isoformat()
        return result

    @app.post('/api/v1/devices/{device_id}/auth-check', dependencies=[Depends(authorized)])
    async def authenticate(device_id: str, request: Request):
        origin = request.headers.get('origin')
        expected_origin = str(request.base_url).rstrip('/')
        peer_loopback = False
        try:
            peer_loopback = bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
        except ValueError:
            pass
        local = (request.url.scheme == 'http' and request.url.hostname in ('127.0.0.1', '::1', 'localhost') and peer_loopback)
        local_container = (settings.local_console_origin is not None and expected_origin == settings.local_console_origin and origin == settings.local_console_origin)
        secure = request.url.scheme == 'https' and expected_origin in settings.console_origins
        if not (local or local_container or secure) or origin != expected_origin:
            raise HTTPException(403, 'A configured same-origin HTTPS console or trusted localhost is required')
        if device_id not in devices:
            raise HTTPException(404, 'Device not configured')
        if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
            raise HTTPException(415, 'JSON required')
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > 8192:
                raise HTTPException(413, 'Request too large')
        try:
            payload = json.loads(content)
            if not isinstance(payload, dict) or set(payload) - {'account', 'password', 'otp'}:
                raise ValueError()
            if not all(isinstance(payload.get(k), str) and 0 < len(payload[k]) <= 1024 for k in ('account','password')):
                raise ValueError()
            if not isinstance(payload.get('otp',''), str) or len(payload.get('otp','')) > 32:
                raise ValueError()
        except (ValueError, TypeError, UnicodeError):
            # Do not use validation errors that echo sensitive submitted input.
            raise HTTPException(400, 'Invalid credential payload') from None
        now = time.monotonic()
        recent = [t for t in attempts.get(device_id, []) if now-t < 900]
        if device_id in active or len(recent) >= 3:
            raise HTTPException(429, 'Wait before another login check; no automatic retry', headers={'Retry-After':'900'})
        attempts[device_id] = recent + [now]
        active.add(device_id)
        async def perform():
            try:
                return await auth_checker(devices[device_id], payload['account'], payload['password'], payload.get('otp',''))
            except ProbeError as exc:
                return {'authentication':'not_attempted', **exc.public()}
            except Exception:
                # Never expose upstream exceptions, which can include request data.
                return {'authentication':'indeterminate', 'logout':'unconfirmed', 'error':'auth_check_failed'}
            finally:
                payload.clear()
                active.discard(device_id)
        task = asyncio.create_task(perform())
        pending.add(task)
        task.add_done_callback(pending.discard)
        # A browser disconnect must not cancel cleanup/logout after a successful login.
        return await asyncio.shield(task)

    @app.get('/')
    async def console():
        return FileResponse(ROOT/'web/index.html')

    app.mount('/assets', StaticFiles(directory=ROOT/'web'), name='assets')
    return app
