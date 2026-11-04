"""Only run against a fresh synthetic local pilot, never a live Connect deployment."""
import os,json,shutil
import openpyxl
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
URL=os.environ.get('OLSD_PILOT_TEST_URL','http://127.0.0.1:3010')
checks=[]
def check(ok,label):
 assert ok,label
 checks.append(label)
with sync_playwright() as w:
 b=w.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
 context=b.new_context(accept_downloads=True);p=context.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_default_timeout(15000)
 p.goto(URL);expect(p.get_by_role('heading',name='Catalog worklist')).to_be_visible()
 def cmd(action,id=None,field=None):
  selector=f'[data-command="{action}"]'
  if id is not None:selector+=f'[data-id="{id}"]'
  if field is not None:selector+=f'[data-field="{field}"]'
  p.locator(selector).first.click();p.wait_for_timeout(250)
 cmd('snapshot');p.locator('#snapshot_file').set_input_files(os.environ.get('OLSD_PILOT_FIXTURE','/tmp/olsd-pilot-snapshot.xlsx'));expect(p.locator('[data-command="accept_snapshot"]')).to_be_visible();cmd('accept_snapshot')
 expect(p.get_by_text('Snapshot accepted. Review affected tests.',exact=True).first).to_be_visible();check(True,'OLSD upload preview and explicit acceptance')
 cmd('mappings');p.locator('#section').fill('CHEM');p.locator('#public_lab').fill('Main lab');p.locator('#category').fill('Chemistry');cmd('save_mapping')
 expect(p.get_by_text('Mapping saved. Affected tests require review.',exact=True).first).to_be_visible()
 cmd('worklist');expect(p.locator('[data-command="open"]')).to_have_count(2);check(True,'Two tests appear once each after source and mapping application')
 second=context.new_page();second.goto(URL);expect(second.get_by_role('heading',name='Catalog worklist')).to_be_visible()
 second.locator('[data-command="open"][data-id="2"]').click();second.locator('input[name="choice_name"][value="olsd"]').check();second.locator('[data-command="save"]').click()
 expect(second.get_by_text('Another browser session has editing control. Close it before taking control here.',exact=False)).to_be_visible();check(True,'A second browser session cannot write shared state');second.close()

 cmd('open','1');expect(p.get_by_role('heading',name='Test 1',exact=True)).to_be_visible();expect(p.get_by_text('Epic link: Blood',exact=True)).to_be_visible();expect(p.get_by_text('This Epic procedure links to multiple OLSD entries.',exact=False)).to_be_visible();check(True,'Shared procedure context and link label are shown without replacing the OLSD name')
 expect(p.locator('[data-command="approve"]')).to_have_count(0);check(True,'An undecided test cannot be approved')
 p.locator('input[name="choice_name"][value="epic"]').check();p.locator('#note_name').fill('Pilot reviewer note');cmd('save')
 expect(p.locator('[data-command="approve"]')).to_be_visible();expect(p.get_by_text('Pilot reviewer note',exact=True).first).to_be_visible();check(True,'Save records the decision and note without approval')
 p.screenshot(path='/tmp/olsd-pilot-review.png',full_page=True)
 cmd('approve','1');expect(p.get_by_text('Selected tests approved. Approval does not upload or publish to OLSD.',exact=True).first).to_be_visible()
 cmd('worklist');cmd('tab','To download');expect(p.locator('[data-command="open"]')).to_have_count(1)
 p.locator('.row-select[value="1"]').check();cmd('prepare');expect(p.locator('#file_1')).to_be_visible()
 check(p.locator('h3').filter(has_text='OLSD_T1').count()==0,'Preparing does not record a download')
 with p.expect_download() as download:p.locator('#file_1').click()
 download.value.save_as('/tmp/olsd-pilot-downloaded.xlsx');wb=openpyxl.load_workbook('/tmp/olsd-pilot-downloaded.xlsx');data=list(wb['Tests'].values);check(data[1][data[0].index('Test Name')]=='New name 1','Downloaded workbook uses approved values');expect(p.get_by_text('Nothing has reached OLSD yet.',exact=True).first).to_be_visible();check(True,'Separate Excel download records initiation')
 p.reload();expect(p.get_by_role('heading',name='Downloads',exact=True)).to_be_visible();check(True,'Refresh preserves the current view');cmd('worklist');cmd('tab','To review');expect(p.locator('[data-command="open"]')).to_have_count(1);check(True,'Saved state survives a new browser session')
 cmd('open','2');p.locator('#value_name').fill('Careful custom wording');p.locator('#note_name').fill('A new unsaved reason');cmd('back')
 expect(p.get_by_role('dialog')).to_be_visible();expect(p.get_by_role('dialog').get_by_text('Careful custom wording',exact=True)).to_be_visible();check(True,'Leaving unsaved work shows its exact proposed wording')
 cmd('stay');expect(p.locator('#note_name')).to_have_value('A new unsaved reason');check(True,'Staying preserves unsaved wording and notes')
 cmd('save');expect(p.get_by_text('A new unsaved reason',exact=True).first).to_be_visible();check(True,'Typing selects custom wording and saves its new note')
 p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(200)
 check(p.evaluate('document.documentElement.scrollWidth<=window.innerWidth+4'),'Test editor fits a phone viewport')
 check(not errors,'No browser JavaScript exceptions')
 Path('/tmp/olsd-pilot-browser-results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'errors':errors},indent=2))
 print(json.dumps({'passed':len(checks),'checks':checks},indent=2));b.close()
