import asyncio
import contextlib
import io
import unittest
import httpx
from backend.config import Device
from backend.dsm import DsmProbe
from backend.diagnose import diagnose, main

D = Device('lab','Lab','https://nas.example.invalid:5001')
class DiagnosisTests(unittest.TestCase):
    def test_proxy_is_not_reported_as_nas_http_403(self):
        def denied(r): raise httpx.ProxyError('403 Forbidden proxy credential not to disclose')
        report, code = asyncio.run(diagnose(D,DsmProbe(httpx.MockTransport(denied))))
        self.assertEqual(code,2)
        self.assertEqual(report['stage'],'proxy')
        self.assertNotIn('http_status',report)
        self.assertEqual(report['authentication'],'not_attempted')
        self.assertNotIn('credential',str(report))

    def test_target_http_error_is_distinguished_from_proxy_failure(self):
        probe=DsmProbe(httpx.MockTransport(lambda r:httpx.Response(403)))
        report,code=asyncio.run(diagnose(D,probe))
        self.assertEqual(report['stage'],'http')
        self.assertEqual(report['http_status'],403)
        self.assertEqual(code,2)

    def test_bad_inventory_cli_has_nonzero_exit_without_traceback(self):
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):
            code=main(['--config','/missing/inventory.json','--device','lab'])
        self.assertEqual(code,1)
        self.assertIn('configuration',capture.getvalue())
