"""UI smoke checks against the real local HTTP API through a browser test bridge.

Build environment blocks browser navigation to every host. This harness loads the
unchanged HTML/CSS/JS into Chromium and relays fetch calls to the real Python server
with http.client. HTTP transport/security is independently covered by test_http.
No hard-coded responses, stats or model results are used. Requires Playwright and
an installed Chromium. Run after starting the app on port 8765.
"""
from __future__ import annotations
import argparse
import http.client
import json
import re
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from fourth_down.data import ROOT


def run(executable: str | None = None) -> dict:
    checks=[];errors=[]
    def relay(path,options):
        c=http.client.HTTPConnection('127.0.0.1',8765,timeout=45)
        c.request(options.get('method','GET'),path,body=options.get('body'),headers=options.get('headers',{}))
        r=c.getresponse();data=r.read().decode();status=r.status;c.close()
        return {'status':status,'body':data}
    def ok(label, condition=True):
        assert condition,label
        checks.append(label)
    with sync_playwright() as p:
        options={'headless':True}
        if executable:options['executable_path']=executable
        browser=p.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1440,'height':1080})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.expose_function('__apiBridge',relay)
        html=(ROOT/'app/index.html').read_text()
        html=re.sub(r'<link[^>]*>','',html);html=re.sub(r'<script[^>]*></script>','',html)
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'app/style.css').read_text())
        page.add_script_tag(content='window.fetch=async function(path,options={}){const r=await window.__apiBridge(path,{method:options.method||"GET",body:options.body,headers:options.headers||{}});return new Response(r.body,{status:r.status,headers:{"Content-Type":"application/json"}});};')
        page.add_script_tag(content=(ROOT/'app/app.js').read_text())
        page.wait_for_selector('.lineup-row')
        def settled():page.wait_for_function('document.querySelector("#busy").hidden === true');page.wait_for_timeout(75)
        settled()
        ok('Initial legal starting seven',page.locator('.lineup-row').count()==7)
        baseline=page.locator('.stat-value').first.inner_text()
        ok('No desktop horizontal overflow',not page.evaluate('document.documentElement.scrollWidth>innerWidth'))
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/lineup.png'),full_page=True)
        page.locator('[data-scoring="ppr"]').click();settled()
        ok('PPR changes the projected total',page.locator('.stat-value').first.inner_text()!=baseline)
        page.locator('[data-scoring="half"]').click();settled()
        ok('Half PPR restores deterministic total',page.locator('.stat-value').first.inner_text()==baseline)
        page.locator('#playerSearch').fill('Mixon');ok('Search filters rows',page.locator('#rosterBody tr').count()==1)
        page.locator('#playerSearch').fill('')
        page.locator('[data-exclude="00-0033897"]').click();settled()
        ok('Manual unavailable flag removes player from lineup','Joe Mixon' not in page.locator('.lineup-rows').inner_text())
        page.locator('[data-action="reset"]').click();settled()
        page.locator('[data-action="reveal"]').click();page.wait_for_selector('dialog[open]')
        ok('Results reveal opens only on request',page.locator('#resultsContent .results-grid').count()==8)
        page.locator('#closeDialog').click();ok('Result modal closes',not page.locator('dialog').is_visible())
        with page.expect_download() as d:
            page.locator('[data-action="export"]').click()
        ok('Lineup CSV export',d.value.suggested_filename.endswith('-lineup.csv'))
        page.locator('#nav [data-view="waivers"]').click();settled()
        ok('Waiver scenarios computed',page.locator('.waiver-card').count()>0)
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/waivers.png'),full_page=True)
        page.locator('[data-add]').first.click();settled()
        ok('Pickup changes example roster and returns to lineup',page.locator('#breadcrumb').inner_text()=='LINEUP LAB')
        page.locator('[data-action="reset"]').click();settled()
        page.locator('#nav [data-view="compare"]').click();settled()
        ok('Player comparison shows two histories',page.locator('.compare-card').count()==2 and page.locator('svg.chart circle').count()>5)
        page.locator('[data-compare="0"]').select_option('00-0030506')
        ok('Player selection updates detail','Travis Kelce' in page.locator('.compare-card').first.inner_text())
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/compare.png'),full_page=True)
        page.locator('#nav [data-view="audit"]').click();settled()
        ok('Audit displays three baselines',page.locator('.audit-table tbody tr').count()==3)
        ok('Audit discloses missing outcomes','Unknown outcomes'.lower() in page.locator('#view').inner_text().lower())
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/audit.png'),full_page=True)
        with page.expect_download() as d:
            page.locator('[data-action="audit-export"]').click()
        ok('Audit CSV export',d.value.suggested_filename.endswith('-audit.csv'))
        page.locator('#nav [data-view="pipeline"]').click();settled()
        ok('Cloud execution limitations visible','NOT CLOUD-EXECUTED' in page.locator('#view').inner_text())
        ok('Source fingerprint visible',page.locator('.hash').inner_text()!='')
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/pipeline.png'),full_page=True)
        page.locator('#nav [data-view="lineup"]').click();settled()
        page.locator('#risk').select_option('steady');settled()
        ok('Steadier preference shows separate objective','Steadiness objective' in page.locator('#view').inner_text())
        page.locator('#risk').select_option('points');settled()
        page.locator('#week').select_option('14');settled()
        ok('Week control changes cutoff',page.locator('#heroWeek').inner_text()=='14')
        ok('Bye player not selected','Derrick Henry' not in page.locator('.lineup-rows').inner_text())
        page.locator('#week').select_option('13');settled()
        page.locator('[data-action="reset"]').click();settled()
        # Deliberately make the roster infeasible.
        page.locator('[data-roster="00-0023459"]').uncheck();settled()
        page.locator('[data-roster="00-0026498"]').uncheck();settled()
        ok('Infeasible roster is explained','Not enough eligible players' in page.locator('.lineup-panel').inner_text())
        ok('Infeasible roster export disabled',page.locator('[data-action="export"]').is_disabled())
        page.locator('[data-action="reset"]').click();settled()
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100)
        ok('No mobile horizontal overflow',not page.evaluate('document.documentElement.scrollWidth>innerWidth'))
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0); document.querySelector("#toast").hidden=true');page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'docs/screenshots/mobile.png'),full_page=True)
        for view in ['waivers','compare','audit','pipeline']:
            page.locator(f'#nav [data-view="{view}"]').click();settled()
            ok(f'{view} mobile fits viewport',not page.evaluate('document.documentElement.scrollWidth>innerWidth'))
        ok('No uncaught JavaScript errors',not errors)
        browser.close()
    report={'checks_passed':len(checks),'checks':checks,'javascript_errors':errors,
            'browser':'Chromium, headless','desktop_viewport':[1440,1080],'mobile_viewport':[390,844],
            'transport':'HTML/CSS/JS injection plus a fetch-to-real-local-HTTP bridge; direct browser navigation blocked by environment policy.',
            'not_tested':['Direct browser-to-loopback navigation in this managed environment','Browser localStorage persistence (opaque test origin)','AWS deployment','Databricks execution']}
    (ROOT/'reports/browser-tests.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium',default=shutil.which('chromium'))
    args=parser.parse_args()
    print(json.dumps(run(args.chromium),indent=2))
