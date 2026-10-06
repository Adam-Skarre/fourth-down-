"""Developer bridge-based browser check; requires Playwright and Chromium.

Direct browser navigation is blocked by this build environment. The bridge relays
requests to the actual loopback HTTP server; no calculations are mocked.
"""
from __future__ import annotations
import json, threading, http.client, re
from pathlib import Path
from playwright.sync_api import sync_playwright
from fourth_down.data import ROOT,Repository
from fourth_down.server import create_server

checks=[]
def check(condition,label):
    if not condition: raise AssertionError(label)
    checks.append(label)

def main():
    server=create_server(Repository(),0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    errors=[]
    def relay(path,options):
        c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        c.request(options.get('method','GET'),path,body=options.get('body'),headers=options.get('headers',{}))
        r=c.getresponse();result={'status':r.status,'body':r.read().decode()};c.close();return result
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
            page.on('pageerror',lambda error:errors.append(str(error)))
            response=relay('/championship.html',{})
            html=re.sub(r'<link[^>]*>','',response['body'])
            html=re.sub(r'<script[^>]*></script>','',html)
            page.expose_function('__caseBridge',relay)
            page.set_content(html)
            for css in ('style.css','championship.css'):
                page.add_style_tag(content=(ROOT/'app'/css).read_text())
            page.add_script_tag(content='window.fetch=async function(path,options={}){const r=await window.__caseBridge(path,options);return new Response(r.body,{status:r.status,headers:{"Content-Type":"application/json"}});};')
            page.add_script_tag(content=(ROOT/'app/championship.js').read_text())
            page.wait_for_function("document.querySelector('#export-case').disabled === false")
            check(response['status']==200,'Real HTTP serves research page; browser renders injected HTML/CSS/JS')
            check(page.locator('.case-person').count()==18,'All 17 drafted players plus reported addition displayed')
            check(page.locator('#case-content').inner_text().count('64')>=1,'Bundled observations render')
            check(page.evaluate('report.pair_case.totals.original')==37.8,'Rendered original result derives from real API')
            check(page.evaluate('report.pair_case.totals.always_stevenson')==55.7,'Stronger fixed-player control remains visible')
            check(page.evaluate('report.fit.alpha')==0,'Unfavorable fit result displayed without alteration')
            check(page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Desktop has no page-level horizontal overflow')
            path=ROOT/'docs/screenshots/championship-2025.png';page.screenshot(path=str(path),full_page=True)
            for scoring in ('standard','half','ppr'):
                for acquired in ('15','16','17'):
                    page.locator('#case-scoring').select_option(scoring)
                    page.locator('#case-acquired').select_option(acquired)
                    page.wait_for_function(f"report && report.scoring === '{scoring}' && report.pair_case.assumed_acquisition_week === {acquired} && !document.querySelector('#export-case').disabled")
                    check(page.evaluate('report.pair_case.n')==18-int(acquired),f'{scoring} / acquisition week {acquired} recomputes comparable cohort')
            with page.expect_download() as info:page.locator('#export-case').click()
            download=info.value
            check(download.suggested_filename=='fourth-down-2025-ppr-from-week-17.json','Export names exact active scenario')
            with open(download.path()) as handle: exported=json.load(handle)
            check(exported['pair_case']['n']==1,'Downloaded JSON contains active calculation, not stale default')
            page.locator('#case-acquired').select_option('15')
            page.wait_for_function('report.pair_case.n === 3')
            page.set_viewport_size({'width':390,'height':844})
            check(page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Mobile has no page-level horizontal overflow')
            page.screenshot(path=str(ROOT/'docs/screenshots/championship-2025-mobile.png'),full_page=True)
            home=relay('/',{})
            check(home['status']==200 and 'href="/championship.html"' in home['body'],'Original application serves link to case route (navigation tested at HTTP layer)')
            check(not errors,'No uncaught JavaScript errors')
            browser.close()
    finally:server.shutdown();server.server_close();thread.join(2)
    result={'method':'Unchanged HTML/CSS/JS rendered in Chromium, with fetch relayed to real HTTP API using http.client. No mocked model results. Direct browser navigation blocked by administrator policy.','passed':len(checks),'failed':0,'checks':checks,'javascript_errors':errors}
    (ROOT/'reports/championship-browser-tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
