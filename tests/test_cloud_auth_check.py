import asyncio
import unittest
from unittest.mock import AsyncMock
from backend.cloud_auth_check import run

class CloudAuthTests(unittest.TestCase):
    def test_missing_bindings_make_no_network_call(self):
        checker=AsyncMock()
        result,code=asyncio.run(run({},checker))
        self.assertEqual(code,1);self.assertEqual(result['authentication'],'not_attempted')
        checker.assert_not_awaited()
    def test_fixed_target_and_no_secret_in_result(self):
        checker=AsyncMock(return_value={'authentication':'succeeded','logout':'confirmed','permissions':'not_tested'})
        result,code=asyncio.run(run({'NAS_SITE_ACCOUNT':'FAKE-ACCOUNT','NAS_SITE_PASSWORD':'FAKE-PASSWORD'},checker))
        self.assertEqual(code,0)
        self.assertEqual(checker.await_args.args[0].endpoint,'https://nassite.hbcg.vn:5001')
        self.assertNotIn('FAKE',str(result))
        self.assertEqual(checker.await_args.kwargs,{'encoding':'multipart'})
    def test_exceptions_are_redacted(self):
        checker=AsyncMock(side_effect=RuntimeError('FAKE-PASSWORD'))
        result,code=asyncio.run(run({'NAS_SITE_ACCOUNT':'FAKE-ACCOUNT','NAS_SITE_PASSWORD':'FAKE-PASSWORD'},checker))
        self.assertEqual(code,2);self.assertNotIn('FAKE',str(result))
