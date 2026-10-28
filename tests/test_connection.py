import unittest
import httpx
from fastapi.testclient import TestClient
from backend.config import Device, Settings
from backend.dsm import DsmProbe
from backend.main import create_app

TOKEN = 'test-only-' + 'x'*40
DEVICE = Device('lab', 'NAS lab', 'https://nas.example.invalid:5001')
GOOD = {'success':True,'data':{'SYNO.API.Auth':{'minVersion':1,'maxVersion':7},'SYNO.FileStation.Info':{'minVersion':1,'maxVersion':2}}}

class ConfigTests(unittest.TestCase):
    def test_reject_invalid_origins(self):
        for url in ['http://nas.example','https://user:pass@nas.example','https://nas.example/path','https://nas.example?x=1','https://127.0.0.1','https://169.254.169.254','https://[::1]','https://localhost','https://0.0.0.0','https://nas.example:0']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                Device('lab','Lab',url)

    def test_private_network_targets_supported(self):
        self.assertEqual(Device('lan','LAN','https://192.168.10.20:5001').id,'lan')

    def test_route_is_metadata_not_a_vpn_client(self):
        d=Device('lan','LAN','https://192.168.10.20:5001',route='vpn')
        self.assertEqual(d.public()['route'],'vpn')
        with self.assertRaises(ValueError):
            Device('qc','QC','https://nas.example',route='quickconnect')

    def test_duplicate_id_and_weak_token_rejected(self):
        with self.assertRaises(ValueError): Settings('weak',())
        with self.assertRaises(ValueError): Settings(TOKEN,(DEVICE,DEVICE))

class ApiTests(unittest.TestCase):
    def client(self, handler):
        probe = DsmProbe(httpx.MockTransport(handler))
        return TestClient(create_app(Settings(TOKEN,(DEVICE,)),probe))

    def headers(self): return {'Authorization':'Bearer '+TOKEN}

    def test_no_auth_cannot_read_or_probe(self):
        calls=[]
        with self.client(lambda r: calls.append(r)) as c:
            self.assertEqual(c.get('/api/v1/devices').status_code,401)
            self.assertEqual(c.post('/api/v1/devices/lab/probe').status_code,401)
            self.assertEqual(c.get('/api/v1/devices',headers={'Authorization':'Bearer wrong'}).status_code,401)
            self.assertEqual(calls,[])

    def test_inventory_and_missing_target(self):
        with self.client(lambda r: httpx.Response(200,json=GOOD)) as c:
            r=c.get('/api/v1/devices',headers=self.headers())
            self.assertEqual(r.status_code,200)
            self.assertNotIn('ca_file',r.text)
            self.assertEqual(c.post('/api/v1/devices/unknown/probe',headers=self.headers()).status_code,404)

    def test_probe_only_queries_public_api_discovery(self):
        def handler(r):
            self.assertEqual(r.method,'GET')
            self.assertEqual(r.url.path,'/webapi/query.cgi')
            self.assertEqual(r.url.params['api'],'SYNO.API.Info')
            self.assertNotIn('passwd',r.url.params)
            self.assertNotIn('authorization',r.headers)
            return httpx.Response(200,json=GOOD)
        with self.client(handler) as c:
            r=c.post('/api/v1/devices/lab/probe',headers=self.headers())
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.json()['authentication'],'not_tested')
            self.assertEqual(r.json()['capabilities'][0]['status'],'advertised_not_authorized')
            self.assertIn('observed_at',r.json())

    def test_redirect_refused_without_following(self):
        calls=[]
        def handler(r):
            calls.append(r)
            return httpx.Response(302,headers={'Location':'https://169.254.169.254/'})
        with self.client(handler) as c:
            r=c.post('/api/v1/devices/lab/probe',headers=self.headers())
            self.assertEqual(r.json()['error'],'redirect_refused')
            self.assertEqual(len(calls),1)

    def test_invalid_responses_and_size_limit(self):
        for response,code in [(httpx.Response(200,text='<html>login</html>'),'dsm_response_invalid'),(httpx.Response(200,json={'success':False}),'dsm_response_invalid'),(httpx.Response(200,json={'success':True,'data':{}}),'dsm_response_invalid'),(httpx.Response(200,json={'success':True,'data':{'SYNO.API.Auth':{'minVersion':5,'maxVersion':1}}}),'dsm_response_invalid'),(httpx.Response(500),'http_error'),(httpx.Response(200,content=b'x'*262145),'response_too_large')]:
            with self.subTest(code=code), self.client(lambda r:response) as c:
                result=c.post('/api/v1/devices/lab/probe',headers=self.headers())
                self.assertEqual(result.status_code,502)
                self.assertEqual(result.json()['error'],code)

    def test_network_errors_sanitized(self):
        for exception,code in [(httpx.ConnectTimeout('secret-proxy-value'),'timeout'),(httpx.ConnectError('CERTIFICATE_VERIFY_FAILED secret'),'tls_verification_failed'),(httpx.ConnectError('sensitive-route'),'connection_failed'),(httpx.ProxyError('proxy-secret'),'proxy_refused')]:
            def handler(r): raise exception
            with self.subTest(code=code),self.client(handler) as c:
                result=c.post('/api/v1/devices/lab/probe',headers=self.headers())
                self.assertEqual(result.json()['error'],code)
                self.assertNotIn('secret',result.text)
                self.assertNotIn('sensitive-route',result.text)

    def test_health_does_not_claim_nas_ready(self):
        with self.client(lambda r:httpx.Response(200,json=GOOD)) as c:
            self.assertEqual(c.get('/healthz').json()['nas_readiness'],'not_verified')
            r=c.get('/')
            self.assertEqual(r.status_code,200)
            self.assertIn("frame-ancestors 'none'",r.headers['content-security-policy'])
            self.assertEqual(r.headers['cache-control'],'no-store')
            self.assertEqual(c.get('/assets/app.js').status_code,200)

if __name__=='__main__': unittest.main()
