import json
import unittest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from backend.config import Device, Settings
from backend.main import create_app
TOKEN='test-only-'+'x'*40
ORIGIN='https://console.example.invalid'
DEVICE=Device('lab','Lab','https://nas.example.invalid:5001')

class AuthFormTests(unittest.TestCase):
    def setup_client(self, checker=None, origin=ORIGIN):
        self.checker=checker or AsyncMock(return_value={'authentication':'succeeded','logout':'confirmed','permissions':'not_tested'})
        return TestClient(create_app(Settings(TOKEN,(DEVICE,),(ORIGIN,)),auth_checker=self.checker),base_url=origin)
    def headers(self,origin=ORIGIN):return {'Authorization':'Bearer '+TOKEN,'Origin':origin}
    def payload(self):return {'account':'test','password':'SECRET-PASS','otp':'123456'}

    def test_unauthorized_never_reaches_checker(self):
        with self.setup_client() as c:
            r=c.post('/api/v1/devices/lab/auth-check',json=self.payload())
            self.assertEqual(r.status_code,401);self.checker.assert_not_awaited()

    def test_same_origin_https_once_no_secrets_returned(self):
        with self.setup_client() as c:
            r=c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers())
            self.assertEqual(r.status_code,200);self.assertEqual(r.json()['logout'],'confirmed')
            self.assertNotIn('SECRET',r.text);self.assertNotIn('123456',r.text)
            self.checker.assert_awaited_once_with(DEVICE,'test','SECRET-PASS','123456')
            self.assertEqual(r.headers['cache-control'],'no-store')
            self.assertIn('Strict-Transport-Security',r.headers)

    def test_plain_http_is_blocked_even_with_key(self):
        with self.setup_client(origin='http://console.example.invalid') as c:
            r=c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers('http://console.example.invalid'))
            self.assertEqual(r.status_code,403);self.checker.assert_not_awaited()

    def test_foreign_or_missing_origin_is_blocked(self):
        with self.setup_client() as c:
            for headers in [self.headers('https://evil.example'),{'Authorization':'Bearer '+TOKEN}]:
                self.assertEqual(c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=headers).status_code,403)
            self.checker.assert_not_awaited()

    def test_validation_never_echoes_submitted_password(self):
        with self.setup_client() as c:
            for value in [{'password':'SECRET-PASS'},dict(self.payload(),otp=['SECRET-PASS']),dict(self.payload(),extra='SECRET-PASS')]:
                r=c.post('/api/v1/devices/lab/auth-check',json=value,headers=self.headers())
                self.assertEqual(r.status_code,400);self.assertNotIn('SECRET',r.text)
            r=c.post('/api/v1/devices/lab/auth-check',content='{"password":"SECRET-PASS"',headers={**self.headers(),'Content-Type':'application/json'})
            self.assertEqual(r.status_code,400);self.assertNotIn('SECRET',r.text)
            self.checker.assert_not_awaited()

    def test_body_limit_and_content_type(self):
        with self.setup_client() as c:
            r=c.post('/api/v1/devices/lab/auth-check',content='x'*8193,headers={**self.headers(),'Content-Type':'application/json'})
            self.assertEqual(r.status_code,413)
            self.assertEqual(c.post('/api/v1/devices/lab/auth-check',content='password=SECRET',headers=self.headers()).status_code,415)
            self.checker.assert_not_awaited()

    def test_three_attempt_limit_no_automatic_retry(self):
        with self.setup_client() as c:
            for _ in range(3):self.assertEqual(c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers()).status_code,200)
            self.assertEqual(c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers()).status_code,429)
            self.assertEqual(self.checker.await_count,3)

    def test_upstream_exception_is_redacted(self):
        checker=AsyncMock(side_effect=RuntimeError('SECRET-PASS 123456'))
        with self.setup_client(checker) as c:
            r=c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers())
            self.assertEqual(r.json()['authentication'],'indeterminate')
            self.assertNotIn('SECRET',r.text);self.assertNotIn('123456',r.text)

    def test_unknown_device_does_not_receive_password(self):
        with self.setup_client() as c:
            self.assertEqual(c.post('/api/v1/devices/unknown/auth-check',json=self.payload(),headers=self.headers()).status_code,404)
            self.checker.assert_not_awaited()

    def test_container_local_mode_requires_exact_origin_and_key(self):
        checker=AsyncMock(return_value={'authentication':'succeeded','logout':'confirmed'})
        app=create_app(Settings(TOKEN,(DEVICE,),local_console_origin='http://127.0.0.1:8080'),auth_checker=checker)
        with TestClient(app,base_url='http://127.0.0.1:8080') as c:
            self.assertEqual(c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers('http://127.0.0.1:8080')).status_code,200)
            self.assertEqual(c.post('/api/v1/devices/lab/auth-check',json=self.payload(),headers=self.headers('http://attacker.example')).status_code,403)
        checker.assert_awaited_once()

    def test_container_mode_cannot_allow_arbitrary_plaintext_origin(self):
        with self.assertRaises(ValueError):Settings(TOKEN,(DEVICE,),local_console_origin='http://public.example')
