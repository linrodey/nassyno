"""Read-only discovery; no login, hidden API, SSH or device mutations."""
import asyncio
import ssl
import re
import httpx
from .config import Device

class ProbeError(Exception):
    def __init__(self, code: str, http_status=None):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.stage = {
            'proxy_refused': 'proxy', 'network_or_proxy_error': 'network',
            'timeout': 'network', 'connection_failed': 'network',
            'tls_verification_failed': 'tls', 'redirect_refused': 'http',
            'http_error': 'http', 'response_too_large': 'http',
            'dsm_response_invalid': 'api',
        }.get(code, 'unknown')

    def public(self):
        result = {'error': self.code, 'stage': self.stage}
        if self.http_status is not None:
            result['http_status'] = self.http_status
        return result

class DsmProbe:
    def __init__(self, transport=None):
        self.transport = transport
        self.semaphore = asyncio.Semaphore(4)

    async def probe(self, device: Device):
        context = ssl.create_default_context(cafile=device.ca_file)
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(verify=context, transport=self.transport,
                        timeout=httpx.Timeout(8, connect=4), follow_redirects=False) as client:
                    async with client.stream('GET', device.endpoint.rstrip('/')+'/webapi/query.cgi', params={
                        'api':'SYNO.API.Info', 'version':'1', 'method':'query',
                        'query':'SYNO.API.Auth,SYNO.FileStation.Info'}) as response:
                        if 300 <= response.status_code < 400:
                            raise ProbeError('redirect_refused')
                        if response.status_code != 200:
                            raise ProbeError('http_error', response.status_code)
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > 262144:
                                raise ProbeError('response_too_large')
                import json
                payload = json.loads(content)
                if not isinstance(payload, dict) or payload.get('success') is not True or not isinstance(payload.get('data'), dict):
                    raise ProbeError('dsm_response_invalid')
                capabilities = []
                for name in ['SYNO.API.Auth', 'SYNO.FileStation.Info']:
                    item = payload['data'].get(name)
                    if not isinstance(item, dict):
                        continue
                    low, high = item.get('minVersion'), item.get('maxVersion')
                    if type(low) is not int or type(high) is not int or low < 1 or high < low:
                        raise ProbeError('dsm_response_invalid')
                    capabilities.append({'api':name,'min_version':low,'max_version':high,
                                         'status':'advertised_not_authorized',
                                         'path':item.get('path') if isinstance(item.get('path'), str) and re.fullmatch(r'[A-Za-z0-9_-]+\.cgi', item['path']) else None})
                if not any(c['api']=='SYNO.API.Auth' for c in capabilities):
                    raise ProbeError('dsm_response_invalid')
                return {'device_id':device.id, 'status':'reachable', 'tls_verified':True,
                        'authentication':'not_tested', 'capabilities':capabilities}
            except ProbeError:
                raise
            except httpx.TimeoutException:
                raise ProbeError('timeout') from None
            except httpx.ConnectError as exc:
                # Never return upstream exception strings: may contain URLs or proxy details.
                tls = 'CERTIFICATE_VERIFY_FAILED' in str(exc)
                raise ProbeError('tls_verification_failed' if tls else 'connection_failed') from None
            except httpx.ProxyError:
                raise ProbeError('proxy_refused') from None
            except httpx.HTTPError:
                raise ProbeError('network_or_proxy_error') from None
            except (ValueError, TypeError, UnicodeError):
                raise ProbeError('dsm_response_invalid') from None
