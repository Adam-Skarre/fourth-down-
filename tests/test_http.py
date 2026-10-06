from __future__ import annotations
import http.client
import json
import threading
import unittest
from fourth_down.data import Repository
from fourth_down.server import create_server

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=Repository();cls.server=create_server(cls.repo,0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.port=cls.server.server_port
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(2)
    def request(self,path,method='GET',body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=8)
        c.request(method,path,body=body,headers=headers or {})
        r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result
    def test_championship_api(self):
        status,_,data=self.request('/api/championship')
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['data']['records'],64)
    def test_championship_scenario(self):
        status,_,data=self.request('/api/championship?scoring=half&acquired=17')
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['pair_case']['n'],1)
    def test_championship_bad_scoring(self):self.assertEqual(self.request('/api/championship?scoring=bonus')[0],400)
    def test_championship_bad_acquisition(self):self.assertEqual(self.request('/api/championship?acquired=0')[0],400)
    def test_championship_page(self):
        status,headers,data=self.request('/championship.html')
        self.assertEqual(status,200);self.assertIn(b'Your roster.',data)
    def test_championship_assets(self):
        for route in ('/championship.css','/championship.js'):
            self.assertEqual(self.request(route)[0],200)
    def test_health(self):
        status,headers,data=self.request('/api/health')
        self.assertEqual(status,200);self.assertEqual(json.loads(data)['records'],164)
    def test_static_html(self):
        status,headers,data=self.request('/')
        self.assertEqual(status,200);self.assertIn('text/html',headers['Content-Type']);self.assertIn(b'Fourth Down',data)
    def test_snapshot(self):
        status,_,data=self.request('/api/snapshot?season=2024&week=13&scoring=half')
        self.assertEqual(status,200);self.assertEqual(len(json.loads(data)['players']),14)
    def test_invalid_week(self):self.assertEqual(self.request('/api/snapshot?week=99')[0],400)
    def test_unknown_path(self):self.assertEqual(self.request('/unknown')[0],404)
    def test_traversal_blocked(self):self.assertEqual(self.request('/../../data/manifest.json')[0],404)
    def test_host_rebinding_blocked(self):self.assertEqual(self.request('/api/meta',headers={'Host':'evil.example'})[0],403)
    def test_cross_origin_blocked(self):
        self.assertEqual(self.request('/api/solve','POST','{}',{'Content-Type':'application/json','Origin':'https://evil.example'})[0],403)
    def test_wrong_content_type(self):self.assertEqual(self.request('/api/solve','POST','{}',{'Content-Type':'text/plain'})[0],415)
    def test_bad_json(self):self.assertEqual(self.request('/api/solve','POST','{nope',{'Content-Type':'application/json'})[0],400)
    def test_oversized_body(self):self.assertEqual(self.request('/api/solve','POST',' '*65537,{'Content-Type':'application/json'})[0],413)
    def test_solve(self):
        payload={'season':2024,'week':13,'scoring':'half','roster':self.repo.metadata()['default_roster']}
        status,_,data=self.request('/api/solve','POST',json.dumps(payload),{'Content-Type':'application/json'})
        self.assertEqual(status,200);self.assertTrue(json.loads(data)['feasible'])
    def test_security_headers(self):
        _,headers,_=self.request('/')
        self.assertEqual(headers['X-Frame-Options'],'DENY');self.assertIn("script-src 'self'",headers['Content-Security-Policy'])
    def test_source_export(self):
        status,headers,data=self.request('/api/data.csv')
        self.assertEqual(status,200);self.assertIn('text/csv',headers['Content-Type']);self.assertIn(b'player_id,name,position',data)

if __name__=='__main__':unittest.main()
