import asyncio
import unittest
from urllib.parse import parse_qs
import httpx
from backend.auth_check import check_auth
from backend.config import Device
D=Device('lab','Lab','https://nas.example.invalid:5001')
class AuthTests(unittest.TestCase):
    def run_check(self,login,logout=None):
        calls=[]
        def handler(r):
            calls.append(r)
            if r.method=='GET':return httpx.Response(200,json={'success':True,'data':{'SYNO.API.Auth':{'path':'entry.cgi','minVersion':1,'maxVersion':7}}})
            body=parse_qs(r.content.decode());self.assertFalse(r.url.query)
            if body['method']==['login']:return httpx.Response(200,json=login)
            if isinstance(logout,Exception):raise logout
            return httpx.Response(200,json=logout or {'success':True})
        result=asyncio.run(check_auth(D,'demo','SECRET-PASSWORD','123456',httpx.MockTransport(handler)))
        return result,calls
    def test_login_logout_body_only_no_secret_in_result(self):
        result,calls=self.run_check({'success':True,'data':{'sid':'SECRET-SID','synotoken':'SECRET-CSRF'}})
        self.assertEqual(result['authentication'],'succeeded');self.assertEqual(result['logout'],'confirmed')
        self.assertNotIn('SECRET',str(result));self.assertEqual(len(calls),3)
        body=parse_qs(calls[-1].content.decode());self.assertEqual(body['_sid'],['SECRET-SID']);self.assertEqual(body['SynoToken'],['SECRET-CSRF'])
    def test_rejected_login_not_retried(self):
        result,calls=self.run_check({'success':False,'error':{'code':403}})
        self.assertEqual(result['dsm_error_code'],403);self.assertEqual(len(calls),2)
    def test_logout_failure_not_reported_as_success(self):
        result,calls=self.run_check({'success':True,'data':{'sid':'SECRET-SID'}},httpx.ReadTimeout('sensitive'))
        self.assertEqual(result['logout'],'unconfirmed');self.assertNotIn('sensitive',str(result));self.assertEqual(len(calls),3)
    def test_missing_sid_reported_indeterminate(self):
        result,calls=self.run_check({'success':True,'data':{}})
        self.assertEqual(result['authentication'],'indeterminate');self.assertEqual(len(calls),2)

    def test_multipart_preserves_proxy_placeholders_and_logout(self):
        from email.parser import BytesParser
        from email.policy import default
        calls=[]
        account='{{FAKE-ACCOUNT-BINDING}}';password='{{FAKE-PASSWORD-BINDING}}'
        def handler(r):
            if r.method=='GET':
                return httpx.Response(200,json={'success':True,'data':{'SYNO.API.Auth':{'path':'entry.cgi','minVersion':1,'maxVersion':7}}})
            self.assertFalse(r.url.query)
            message=BytesParser(policy=default).parsebytes(('Content-Type: '+r.headers['content-type']+'\r\n\r\n').encode()+r.content)
            values={part.get_param('name',header='content-disposition'):part.get_payload(decode=True).decode() for part in message.iter_parts()}
            calls.append(values['method'])
            if values['method']=='login':
                self.assertEqual(values['account'],account)
                self.assertEqual(values['passwd'],password)
                return httpx.Response(200,json={'success':True,'data':{'sid':'FAKE-SID'}})
            self.assertEqual(values['_sid'],'FAKE-SID')
            return httpx.Response(200,json={'success':True})
        result=asyncio.run(check_auth(D,account,password,transport=httpx.MockTransport(handler),encoding='multipart'))
        self.assertEqual(calls,['login','logout'])
        self.assertEqual(result['logout'],'confirmed')
        self.assertNotIn('FAKE',str(result))
