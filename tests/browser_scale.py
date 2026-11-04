import os,json,shutil,time,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
metrics=[]
with sync_playwright() as w:
 b=w.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(os.environ['OLSD_PILOT_TEST_URL']);expect(p.get_by_role('heading',name='Catalog worklist')).to_be_visible()
 def click(action,id=None):
  q=f'[data-command="{action}"]'+(f'[data-id="{id}"]' if id else '');p.locator(q).first.click()
 click('tab','All tests');expect(p.locator('[data-command="open"]')).to_have_count(50)
 click('show_more');expect(p.locator('[data-command="open"]')).to_have_count(100)
 click('select_all')
 p.wait_for_function('Shiny.shinyapp.$inputValues.selected?.length===1542')
 p.locator('.row-select').first.uncheck();p.wait_for_function('Shiny.shinyapp.$inputValues.selected?.length===1541')
 click('select_all');p.wait_for_function('Shiny.shinyapp.$inputValues.selected?.length===1542')
 for i in range(4):
  start=time.perf_counter();click('mappings');expect(p.get_by_role('heading',name='Lab mappings',exact=True)).to_be_visible();click('worklist');expect(p.locator('[data-command="open"]')).to_have_count(100);metrics.append(time.perf_counter()-start)
  click('tab','To review');expect(p.locator('[data-command="open"]')).to_have_count(0);click('tab','All tests');expect(p.locator('[data-command="open"]')).to_have_count(50);click('show_more');expect(p.locator('[data-command="open"]')).to_have_count(100)
 assert not errors,errors
 report={'catalog_count':1542,'initial_rows':50,'expanded_rows':100,'bulk_selected':1542,'selection_after_unchecking_one_visible_row':1541,'navigation_round_trip_seconds':metrics,'median_navigation_round_trip_seconds':statistics.median(metrics),'browser_errors':errors}
 Path('/tmp/olsd-pilot-scale-results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));b.close()
