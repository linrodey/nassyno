"""Read-only CLI. Uses the same inventory and verified HTTPS transport as the API."""
import argparse
import asyncio
import json
from pathlib import Path
from .config import Device
from .dsm import DsmProbe, ProbeError

HINTS = {
    'proxy_refused': 'Proxy rejected the connection. Check environment egress policy and destination port; this does not prove a DSM API fault.',
    'network_or_proxy_error': 'Check network/proxy connectivity from the application host.',
    'timeout': 'Check route, DNS, NAT and firewall from the application host.',
    'connection_failed': 'Check endpoint, DNS, route and listening HTTPS port.',
    'tls_verification_failed': 'Use the hostname matching the certificate or configure the trusted CA. Do not disable TLS verification.',
    'redirect_refused': 'Configure the final trusted DSM HTTPS origin; redirects are not followed.',
    'http_error': 'An HTTP service replied with an error; check reverse proxy routing and access rules.',
    'dsm_response_invalid': 'The response was not expected DSM discovery data; check /webapi/ routing and DSM service.',
    'response_too_large': 'The service returned an unexpectedly large response.',
}

async def diagnose(device, probe=None):
    try:
        result = await (probe or DsmProbe()).probe(device)
        result['next_step'] = 'Discovery is reachable. Authentication and permissions still require separate tests.'
        return result, 0
    except ProbeError as exc:
        return {'device_id':device.id, 'status':'failed', **exc.public(),
                'next_step':HINTS.get(exc.code,'Investigate this stage before proceeding.'),
                'authentication':'not_attempted'}, 2

def main(argv=None):
    parser = argparse.ArgumentParser(description='DSM HTTPS discovery, read-only; no credentials accepted')
    parser.add_argument('--config', required=True)
    parser.add_argument('--device', required=True)
    args = parser.parse_args(argv)
    try:
        devices = [Device(**item) for item in json.loads(Path(args.config).read_text())['devices']]
        matches = [d for d in devices if d.id == args.device]
        if len(matches) != 1:
            raise ValueError('Select exactly one configured device')
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'status':'failed','stage':'configuration','error':'invalid_inventory_or_device'}))
        return 1
    result, code = asyncio.run(diagnose(matches[0]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code

if __name__ == '__main__':
    raise SystemExit(main())
