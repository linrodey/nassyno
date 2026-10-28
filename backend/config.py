"""Operator-controlled endpoints only; credentials are not part of inventory."""
import ipaddress
import json
import os
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

@dataclass(frozen=True)
class Device:
    id: str
    name: str
    endpoint: str
    ca_file: str | None = None
    route: str = "public"

    def __post_init__(self):
        if self.route not in ('public', 'vpn', 'lan'):
            raise ValueError('Route must be public, vpn or lan; QuickConnect is not verified yet')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', self.id):
            raise ValueError('Invalid device id')
        u = urlsplit(self.endpoint)
        if (u.scheme != 'https' or not u.hostname or u.username is not None
                or u.password is not None or u.query or u.fragment
                or u.path not in ('', '/') or u.port == 0):
            raise ValueError('Endpoint must be an HTTPS origin without credentials or path')
        try:
            addr = ipaddress.ip_address(u.hostname)
        except ValueError:
            if not re.fullmatch(r'(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?', u.hostname):
                raise ValueError('Invalid hostname')
            if u.hostname.lower() == 'localhost' or u.hostname.lower().endswith('.localhost'):
                raise ValueError('Loopback endpoints are not NAS targets')
        else:
            if addr.is_loopback or addr.is_link_local or addr.is_unspecified or addr.is_multicast:
                raise ValueError('Loopback, link-local and non-unicast targets are forbidden')
        if self.ca_file:
            ssl.create_default_context(cafile=self.ca_file)

    def public(self):
        return {'id': self.id, 'name': self.name, 'endpoint': self.endpoint, 'route': self.route}

@dataclass(frozen=True)
class Settings:
    admin_token: str
    devices: tuple[Device, ...]
    console_origins: tuple[str, ...] = ()
    local_console_origin: str | None = None

    def __post_init__(self):
        if self.local_console_origin not in (None, 'http://127.0.0.1:8080'):
            raise ValueError('Container local console is restricted to http://127.0.0.1:8080')
        for origin in self.console_origins:
            u = urlsplit(origin)
            if u.scheme != 'https' or not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
                raise ValueError('Console origins must be exact HTTPS origins without a trailing slash')
        if len(self.admin_token) < 32:
            raise ValueError('NAS_MANAGER_ADMIN_TOKEN must contain at least 32 characters')
        if len({d.id for d in self.devices}) != len(self.devices):
            raise ValueError('Duplicate device id')

    @classmethod
    def from_env(cls):
        filename = os.environ.get('NAS_MANAGER_CONFIG')
        entries = json.loads(Path(filename).read_text())['devices'] if filename else []
        token_file = os.environ.get('NAS_MANAGER_ADMIN_TOKEN_FILE')
        token = Path(token_file).read_text().strip() if token_file else os.environ.get('NAS_MANAGER_ADMIN_TOKEN', '')
        return cls(token, tuple(Device(**d) for d in entries), tuple(json.loads(os.environ.get('NAS_MANAGER_CONSOLE_ORIGINS', '[]'))), os.environ.get('NAS_MANAGER_LOCAL_CONSOLE_ORIGIN'))
