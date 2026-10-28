"""One login/logout check using platform-provided secrets, fixed authorized NAS only."""
import asyncio
import json
import os
from .auth_check import check_auth
from .config import Device
from .dsm import ProbeError

async def run(environ=None, checker=None):
    source = os.environ if environ is None else environ
    required = ('NAS_SITE_ACCOUNT', 'NAS_SITE_PASSWORD')
    missing = [name for name in required if not source.get(name)]
    if missing:
        return {'authentication':'not_attempted','error':'missing_secret_bindings','missing':missing}, 1
    device = Device('nas-site','NAS SITE','https://nassite.hbcg.vn:5001')
    try:
        result = await (checker or check_auth)(device,source[required[0]],source[required[1]],encoding='multipart')
    except ProbeError as exc:
        return {'authentication':'not_attempted',**exc.public()}, 2
    except Exception:
        return {'authentication':'indeterminate','logout':'unconfirmed','error':'auth_check_failed'}, 2
    passed = result.get('authentication') == 'succeeded' and result.get('logout') == 'confirmed'
    return result, 0 if passed else 2

def main():
    result, code = asyncio.run(run())
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return code

if __name__ == '__main__':
    raise SystemExit(main())
