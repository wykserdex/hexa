import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# Optional developer test. Run against a disposable Lab server: it resets its state.
import argparse
import tempfile
parser = argparse.ArgumentParser(description='HEXA Lab browser smoke test (optional Playwright dependency)')
parser.add_argument('--url', default='http://127.0.0.1:8080')
parser.add_argument('--output', default=None)
args = parser.parse_args()
BASE = args.url.rstrip('/')
ROOT = Path(args.output or tempfile.mkdtemp(prefix='hexa-browser-check-'))
ROOT.mkdir(parents=True, exist_ok=True)
print('Artifacts:', ROOT)
default_config={'version':1,'speed':1,'modules':{'combo':{'enabled':True,'settings':{}},'guardian':{'enabled':True,'settings':{'threshold':40}},'farm':{'enabled':False,'settings':{}},'micro':{'enabled':False,'settings':{}}}}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1060},device_scale_factor=1,accept_downloads=True)
 page=context.new_page()
 errors=[]; requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 def act(**payload):
  r=context.request.post(BASE+'/api/control',data=payload)
  assert r.status==200,(r.status,r.text())
 act(action='import',config=default_config);act(action='reset')
 page.goto(BASE,wait_until='domcontentloaded')
 expect(page.locator('#connection-label')).to_have_text('Движок подключён')
 page.screenshot(path=str(ROOT/'desktop.png'),full_page=True)
 print('Desktop initialized; no horizontal overflow:', page.evaluate('document.documentElement.scrollWidth===innerWidth'))
 page.locator('#combo-button').click()
 page.wait_for_function("() => state.history.filter(c=>c.source==='combo'&&c.status==='executed').length===4")
 assert page.locator('#metric-executed').inner_text()=='4'
 print('Combo button: 4 actual executions')
 page.locator('#damage-button').click()
 page.wait_for_function("() => state.history.some(c=>c.source==='guardian'&&c.status==='executed')")
 print('Damage button: auto item confirmed')
 page.locator('#module-row-farm [role=switch]').click()
 expect(page.locator('#module-row-farm [role=switch]')).to_have_attribute('aria-checked','true')
 page.keyboard.press('Space')
 expect(page.locator('#owner-value')).to_have_text('Игрок')
 print('Toggle and keyboard manual handover work')
 page.locator('a.nav-item[data-page=modules]').click()
 page.locator('#threshold-slider').evaluate("el=>{el.value='55';el.dispatchEvent(new Event('change',{bubbles:true}));}")
 page.wait_for_function('() => state.item.threshold===55')
 with page.expect_download() as d:
  page.locator('#export-config-main').click()
 config_download=d.value
 config_download.save_as(str(ROOT/'exported-config.json'))
 assert json.loads((ROOT/'exported-config.json').read_text())['modules']['guardian']['settings']['threshold']==55
 page.locator('#config-file').set_input_files({'name':'config.json','mimeType':'application/json','buffer':json.dumps(default_config).encode()})
 page.wait_for_function('() => state.item.threshold===40')
 print('Configuration threshold, export and import work')
 for key in ['priority','survival','manual','micro']:
  page.locator('a.nav-item[data-page=scenarios]').click()
  page.locator('[data-scenario='+key+']').click()
  page.wait_for_function("key => state.scenario?.key===key&&state.scenario.status==='passed'",arg=key,timeout=10000)
  print('Browser scenario:', key, 'passed')
 page.locator('a.nav-item[data-page=logs]').click()
 expect(page.locator('#log-body tr').first).to_be_visible()
 page.locator('[data-filter=executed]').click()
 with page.expect_download() as d:
  page.locator('#export-log').click()
 d.value.save_as(str(ROOT/'session-export.json'))
 assert len(json.loads((ROOT/'session-export.json').read_text())['history'])>0
 print('Log filters and JSON export work')
 page.screenshot(path=str(ROOT/'logs.png'),full_page=True)
 page.locator('a.nav-item[data-page=scenarios]').click()
 page.screenshot(path=str(ROOT/'scenarios.png'),full_page=True)
 act(action='import',config=default_config);act(action='reset')
 page.locator('a.nav-item[data-page=overview]').click()
 page.wait_for_function('() => state.metrics.executed===0')
 page.locator('#pause-button').click()
 page.wait_for_function('() => state.paused')
 page.locator('#reset-button').click()
 expect(page.locator('#reset-dialog')).to_be_visible()
 page.locator('#reset-dialog button[value=reset]').click()
 page.wait_for_function('() => !state.paused')
 print('Pause and reset dialog work')
 page.set_viewport_size({'width':390,'height':844})
 page.screenshot(path=str(ROOT/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth===innerWidth'), 'Mobile overflow'
 page.locator('a.nav-item[data-page=modules]').click()
 page.screenshot(path=str(ROOT/'mobile-modules.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth===innerWidth')
 print('Mobile overview/modules: no horizontal overflow')
 # Endpoint input validation and same-origin protections.
 assert context.request.post(BASE+'/api/control',data={'action':'move','x':-1,'y':100}).status==400
 assert context.request.post(BASE+'/api/control',data=[1,2]).status==400
 assert context.request.post(BASE+'/api/control',data='{}',headers={'Content-Type':'text/plain'}).status==415
 assert context.request.post(BASE+'/api/control',data={'action':'combo'},headers={'Sec-Fetch-Site':'cross-site'}).status==403
 assert context.request.get(BASE+'/not-a-file').status==404
 assert not errors, errors
 assert not [url for url in requests if not url.startswith(BASE)],requests
 print('API validation: pass. JS errors:',errors,'. External requests: 0')
 act(action='import',config=default_config);act(action='reset')
 browser.close()
