"""Browser checks for the choose/save/approve/download redesign. Optional argument: case name."""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
import json,hashlib,os,sys,traceback
import openpyxl
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
BASE=os.environ.get('OLSD_TEST_URL','http://127.0.0.1:3000')
ONLY=sys.argv[1] if len(sys.argv)>1 else None
checks=[];errors=[];metrics={};active=''
def check(ok,description):
    if not ok:raise AssertionError(active+': '+description)
    checks.append({'case':active,'description':description,'passed':True})
def open_test(p,id):p.goto(BASE+'/#/test?id='+id);p.locator('h1').wait_for()
def choose(p,k,c):p.locator(f'[data-answer="{k}:{c}"]').click()
def save_button(p):return p.locator('.save-bar .primary')
def approve_one(p,id):p.locator(f'[data-approve="{id}"]').click()
def click_download(p,path):
    with p.expect_download() as info:p.locator('[data-download-ids]').click()
    info.value.save_as(ROOT/path)
    return openpyxl.load_workbook(ROOT/path)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    @contextmanager
    def case(name,size=None):
        global active
        active=name;ctx=browser.new_context(viewport=size or {'width':1450,'height':900},accept_downloads=True)
        p=ctx.new_page();p.set_default_timeout(20000);p.on('pageerror',lambda err:errors.append(str(err)))
        p.goto(BASE);p.locator('h1').wait_for()
        try:yield p
        except Exception:
            traceback.print_exc()
            try:p.screenshot(path=str(ROOT/'review-assets'/('failure-'+name+'.png')),full_page=True,timeout=2000)
            except Exception:pass
            raise
        finally:ctx.close();print('Completed',name,flush=True)
    if ONLY in [None,'five-click-flow']:
        with case('five-click-flow') as p:
            clicks=0
            p.locator('[data-inline="demo-tsh|name|epic"]').click();clicks+=1
            check(p.evaluate("byId('demo-tsh').decisions.name===undefined"),'Choosing Epic does not save the choice')
            check(p.evaluate("state.tests.filter(t=>!!t.approval).length")==1,'Choosing does not create an approval')
            check(p.locator('[data-row="demo-tsh|name"]').is_visible(),'Chosen row stays in its original list position until Save')
            check(p.locator('[data-inline="demo-tsh|name|epic"]').get_attribute('aria-pressed')=='true','Inline choice visibly highlights the selected answer')
            save_button(p).click();clicks+=1
            check(p.evaluate("byId('demo-tsh').decisions.name.choice")=='epic','Save persists the explicit choice')
            check(p.evaluate("byId('demo-tsh').approval===null"),'Saving never approves')
            p.get_by_role('button',name='Go to approvals',exact=True).click();clicks+=1
            p.locator('[data-approve="demo-tsh"]').click();clicks+=1
            check(p.evaluate("approved(byId('demo-tsh'))"),'Approval is a separate deliberate click')
            check(p.locator('[role="dialog"]').count()==0,'Approval does not add a redundant confirmation dialog')
            wb=click_download(p,'tested-v6-single.xlsx');clicks+=1
            rows=list(wb['Tests'].values)
            check(rows[1][rows[0].index('Test Name')]=='TSH, Third Generation','Direct Excel file contains the explicitly chosen name')
            check(clicks==5,'One change reaches a downloaded file in exactly five clicks')
            metrics['single_change_to_download_clicks']=clicks
            check('Next, import this file into OLSD.' in p.locator('.import-next').inner_text(),'After download the real next step is stated')
            check(p.evaluate("state.exports.length")==1,'One file is recorded only after the download action')
    if ONLY in [None,'seven-click-bulk']:
        with case('seven-click-bulk') as p:
            clicks=0
            p.locator('[data-select-section="name"]').click();clicks+=1
            check(p.evaluate('ui.selected.size')==32,'Select all includes the whole 32-name section, not just rendered rows')
            check(p.locator('[data-action="bulk-epic"]').inner_text()=='Use Epic for 32','Bulk action clearly names its number of choices')
            p.locator('[data-action="bulk-epic"]').click();clicks+=1
            check(p.evaluate('unsavedIds().length')==32,'Bulk choice stages 32 choices without saving them')
            check(p.evaluate("state.tests.filter(t=>t.decisions.name?.choice==='epic').length")==0,'Bulk selection never silently persists choices')
            save_button(p).click();clicks+=1
            check(p.evaluate('state.tests.filter(canApprove).length')==32,'Save creates 32 updates waiting for their own approval')
            p.get_by_role('button',name='Go to approvals',exact=True).click();clicks+=1
            p.locator('[data-action="select-all-approvals"]').click();clicks+=1
            check(p.locator('[data-action="approve-all"]').inner_text()=='Approve all 32','Approval page states the exact batch count')
            p.locator('[data-action="approve-all"]').click();clicks+=1
            wb=click_download(p,'tested-v6-32-names.xlsx');clicks+=1
            check(len(list(wb['Tests'].values))==33,'One named workbook contains all 32 accepted names and the header')
            check(clicks==7,'32 name changes reach a file in seven clicks including explicit approval selection')
            metrics['32_name_changes_to_download_clicks']=clicks
            check(p.evaluate('state.exports[0].tests.length')==32,'Downloaded batch records precisely the approved 32 tests')
    if ONLY in [None,'two-click-keep-undo']:
        with case('two-click-keep-undo') as p:
            p.locator('[data-inline="demo-crp|name|olsd"]').click()
            check(p.evaluate("byId('demo-crp').proposed.name")=='C-Reactive Protein','Keep choice does not change the saved data before Save')
            save_button(p).click()
            check(p.evaluate("byId('demo-crp').proposed.name")=='C Reactive Protein','Keep means current catalog text, not an earlier working version')
            check(p.evaluate("!needsReview(byId('demo-crp')) && !canApprove(byId('demo-crp'))"),'Keeping finishes on Save with no approval or file')
            metrics['simple_choice_to_saved_clicks']=2
            p.locator('[data-action="undo-save"]').click()
            check(p.evaluate("needsReview(byId('demo-crp')) && !byId('demo-crp').decisions.name"),'Undo restores the exact pre-save choice and review state')
    if ONLY in [None,'bulk-labs-and-free-text']:
        with case('bulk-labs-and-free-text') as p:
            p.locator('[data-select-section="labs"]').click()
            check(p.evaluate('ui.selected.size')==11,'Editor lab section selects all 11 actionable changes')
            p.locator('[data-action="bulk-epic"]').click();save_button(p).click()
            check(p.evaluate("state.tests.filter(t=>t.decisions.labs?.choice==='epic').length")==11,'Bulk laboratory choices save exactly their intended tests')
            check(p.evaluate('state.tests.filter(canApprove).length')==11,'Bulk saving labs does not approve them')
            p.evaluate("applySnapshot({'785258':{conditions:'New sample catalog conditions'}});render();")
            check(p.locator('[data-select="785258|conditions"]').count()==0,'Free-text changes never offer a bulk-accept checkbox')
            check(p.locator('[data-inline*="conditions"]').count()==0,'Free-text changes never offer inline bulk Epic acceptance')
    if ONLY in [None,'question-cards']:
        with case('question-cards') as p:
            open_test(p,'demo-tsh')
            check(p.locator('.question').count()==1,'A single-change test shows its one question')
            check('TSH, Third Generation' in p.locator('[data-answer="name:epic"]').inner_text(),'Epic answer card contains the real new name')
            check('Thyroid Stimulating Hormone' in p.locator('[data-answer="name:olsd"]').inner_text(),'Keep card contains the real current catalog name')
            check(p.locator('.answer-card[aria-pressed="true"]').count()==0,'No answer is preselected')
            check(p.locator('.save-bar').count()==0,'No always-on disabled save bar appears before a choice')
            choose(p,'name','epic')
            check(p.locator('[data-answer="name:epic"]').is_visible(),'Chosen answer remains visible and changeable before Save')
            choose(p,'name','olsd')
            check(p.evaluate("staged.get('demo-tsh').proposed.name===byId('demo-tsh').olsd.name"),'Changing an unsaved answer updates the staged value only')
            p.locator('[data-action="discard"]').click()
            check(p.evaluate("!byId('demo-tsh').decisions.name && !dirtyNow()"),'Discard removes the unsaved answer without touching saved state')
            check(p.locator('table').count()==0,'The test page uses stacked cards and content instead of a sideways table')
            check(p.locator('[data-entry-field="conditions"]').is_visible(),'Other catalog text is readable without expanding an instruction panel')
    if ONLY in [None,'save-next-and-shortcuts']:
        with case('save-next-and-shortcuts') as p:
            open_test(p,'785258');choose(p,'labs','epic')
            check(save_button(p).inner_text()=='Save' and p.locator('[data-action="save-next"]').is_visible(),'Save stays primary and Save and next is available separately')
            p.locator('[data-action="save-next"]').click()
            check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Save and next moves to the next waiting test')
            check(p.evaluate("byId('785258').approval===null && byId('785258').decisions.labs.choice==='epic'"),'Moving next saves the prior choice without approving it')
            p.keyboard.press('1')
            check(p.locator('[data-answer="name:epic"]').get_attribute('aria-pressed')=='true','Shortcut 1 chooses the actual Epic answer')
            p.keyboard.press('2')
            check(p.locator('[data-answer="name:olsd"]').get_attribute('aria-pressed')=='true','Shortcut 2 chooses the actual current catalog answer')
            p.keyboard.press('Control+s')
            check(p.evaluate("byId('demo-tsh').decisions.name.choice==='olsd' && !dirtyNow()"),'Ctrl+S saves without approving')
            check(p.locator('[data-approve="demo-tsh"]').count()==0,'Saved keep does not offer an unnecessary approval')
    if ONLY in [None,'set-aside-return']:
        with case('set-aside-return') as p:
            open_test(p,'demo-tsh');before=p.evaluate('stageCounts().review')
            choose(p,'name','defer');p.locator('[data-toggle-note="name"]').click();p.locator('#note-name').fill('Ask the laboratory director');save_button(p).click()
            check(p.evaluate('stageCounts().review')==before-1,'Saving Decide later removes the test from To review')
            check(p.evaluate("matches(byId('demo-tsh'),'later')"),'Set-aside choice is findable under All tests')
            p.evaluate("applySource('Epic',{'demo-tsh':{name:'TSH next version'}});refreshWorking();render();")
            check(p.evaluate("needsReview(byId('demo-tsh'))"),'A later Epic change returns the set-aside test to review')
            open_test(p,'demo-tsh')
            check('Ask the laboratory director' in p.locator('.previous-choice').inner_text(),'Prior note and old/new context remain visible')
            check('set this aside' in p.locator('.previous-choice').inner_text(),'A deferred choice is not mislabeled as kept wording')
    if ONLY in [None,'guards-and-role-discard']:
        with case('guards-and-role-discard') as p:
            open_test(p,'demo-tsh');choose(p,'name','epic');p.locator('#role').select_option('admin')
            check(p.get_by_role('dialog').is_visible(),'Leaving an unsaved choice warns before changing role')
            p.get_by_role('button',name='Stay',exact=True).click()
            check(p.locator('#role').input_value()=='editor' and p.evaluate('dirtyNow()'),'Stay restores the role selector and retains the unsaved choice')
            p.locator('#role').select_option('admin');p.get_by_role('dialog').get_by_role('button',name='Discard',exact=True).click()
            check(p.evaluate("state.role==='admin' && !byId('demo-tsh').decisions.name && !dirtyNow()"),'Discard restores saved data before changing role')
            check(p.locator('[data-answer="name:epic"]').get_attribute('aria-pressed')=='false','Discarded choice no longer looks selected')
    if ONLY in [None,'approval-and-send-back']:
        with case('approval-and-send-back') as p:
            open_test(p,'demo-tsh');p.evaluate("try{approveRecord(byId('demo-tsh'));}catch(e){}")
            check(p.evaluate("byId('demo-tsh').approval===null && !byId('demo-tsh').decisions.name"),'Approval guard never invents an undecided Epic choice')
            choose(p,'name','epic');p.keyboard.press('Control+s')
            approve_one(p,'demo-tsh')
            check(p.evaluate("!!byId('demo-tsh').approval.basis.olsd && !!byId('demo-tsh').approval.basis.epic"),'Approval captures both dated sets of values')
            check(p.locator('[role="dialog"]').count()==0,'A visible reviewed change approves without another confirmation')
            p.locator('[data-tab="download"]').count()
            p.goto(BASE+'/#/worklist?tab=download');p.locator('[data-withdraw="demo-tsh"]').click()
            check(p.evaluate("byId('demo-tsh').approval===null && canApprove(byId('demo-tsh'))"),'Withdraw returns the saved update to approval work')
            p.goto(BASE+'/#/worklist?tab=approve');p.locator('[data-send-back="demo-tsh"]').click()
            check(p.evaluate("needsReview(byId('demo-tsh'))"),'Send back returns the update to review')
            open_test(p,'demo-tsh');check('Review this saved test name change' in p.locator('.question h2').inner_text(),'Sent-back catalog edits are not falsely called new Epic changes')
    if ONLY in [None,'download-edits-and-status']:
        with case('download-edits-and-status') as p:
            open_test(p,'785260');p.locator('[data-change-choice="conditions"]').click();p.locator('#edit-conditions').fill('New unsaved rejection wording')
            check(p.locator('[data-download-ids]').count()==0,'Starting an approved edit removes the old download action from that screen')
            check(p.locator('[data-approve="785260"]').count()==0,'Unsaved edits cannot be approved')
            save_button(p).click()
            check(p.evaluate("byId('785260').approval.outdated"),'Saving an approved edit withdraws its old approval')
            approve_one(p,'785260');click_download(p,'tested-v6-edited.xlsx')
            check(p.evaluate("!ready(byId('785260'))"),'Downloaded tests leave To download')
            check(p.evaluate("statusLabel(byId('785260'))")=='Downloaded, import into OLSD','Downloaded test states the import task plainly')
            p.locator('#role').select_option('admin');p.locator('[data-nav="downloads"]').click();p.locator('.admin-comparison > summary').click();p.locator('[data-reconcile$=":match"]').click()
            check(p.evaluate("confirmed(byId('785260'))"),'Later matching catalog marks the test done')
            check(p.evaluate("!matches(byId('785260'),'review') && !matches(byId('785260'),'approve') && !matches(byId('785260'),'download')"),'Done tests leave all active lists')
            check(p.evaluate("statusLabel(byId('785260'))")=='','Up-to-date tests have no unnecessary status label')
    if ONLY in [None,'multiple-files-one-click']:
        with case('multiple-files-one-click') as p:
            p.locator('[data-inline="demo-crp|name|epic"]').click();save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click();p.locator('[data-approve="demo-crp"]').click()
            p.locator('[data-tab="download"]').click()
            p.locator('[data-action="select-all-downloads"]').click()
            check(p.locator('[data-download-ids]').inner_text()=='Download 2 files','Different catalog updates clearly name the number of Excel files')
            check('different parts of the catalog' in p.locator('main').inner_text(),'Separate Excel files have a plain-language explanation')
            downloads=[];p.on('download',lambda d:downloads.append(d))
            p.locator('[data-download-ids]').click();p.wait_for_timeout(300)
            check(len(downloads)==2,'A single explicit click starts both separate Excel files')
            check(p.locator('[role="dialog"]').count()==0,'There is no intermediate chooser or ZIP dialog')
            check(p.evaluate('state.exports.length')==2,'Each file initiated by the explicit download action is recorded')
            for i,d in enumerate(downloads):
                d.save_as(ROOT/f'tested-v6-multi-{i}.xlsx')
                check(openpyxl.load_workbook(ROOT/f'tested-v6-multi-{i}.xlsx').sheetnames==['Tests'],'Each separately downloaded file is valid Excel')
    if ONLY in [None,'snapshot-staleness']:
        with case('snapshot-staleness') as p:
            p.locator('[data-inline="demo-tsh|name|epic"]').click();save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click();p.locator('[data-approve="demo-tsh"]').click()
            basis=p.evaluate("JSON.stringify(byId('demo-tsh').approval.basis)")
            p.evaluate("applySource('Epic',{'demo-tsh':{name:'Another Epic TSH name'}});render();")
            check(p.evaluate("needsReview(byId('demo-tsh')) && !ready(byId('demo-tsh'))"),'Unexpected Epic changes return approved work to To review')
            check(p.evaluate("JSON.stringify(byId('demo-tsh').approval.basis)")==basis,'Approval’s original dated values are retained')
            p.evaluate("applySnapshot({'demo-tsh':{conditions:'Different catalog conditions'}});render();")
            check(p.evaluate("!!byId('demo-tsh').pending.conditions"),'Unselected unexpected catalog content is still a review question')
            open_test(p,'demo-tsh')
            check(p.locator('.question').count()==2,'All open changes are shown together on the test page')
    if ONLY in [None,'custom-wording-and-plain-entry']:
        with case('custom-wording-and-plain-entry') as p:
            open_test(p,'demo-tsh');p.locator('[data-write="name"]').click();p.locator('#edit-name').fill('My public TSH name')
            p.keyboard.press('Control+s')
            check(p.evaluate("byId('demo-tsh').decisions.name.choice==='custom' && retained(byId('demo-tsh'))"),'Typed wording records a deliberate custom choice and remains discoverable')
            p.locator('[data-change-choice="name"]').click();p.locator('#edit-name').fill('My final catalog TSH wording');p.locator('[data-action="see-changes"]').click()
            modal=p.get_by_role('dialog')
            check('My public TSH name' in modal.inner_text() and 'My final catalog TSH wording' in modal.inner_text(),'See changes shows exact before and after wording')
            check(modal.locator('ins').count()>0 and modal.locator('del').count()>0,'Exact unsaved comparison keeps word-level highlighting')
            p.get_by_role('button',name='Continue choosing',exact=True).click();p.locator('[data-action="discard"]').click()
            p.goto(BASE+'/#/test?id=sample-1')
            check(p.locator('[data-entry-field]').count()==4,'A test with no open changes displays its complete catalog entry')
            check(p.locator('.question').count()==0 and p.locator('.save-bar').count()==0,'Unchanged entry has no fake decision or disabled main action')
            check(p.locator('[data-answer]').count()==0,'Unchanged content does not offer Decide later or other meaningless decisions')
            check(p.locator('[data-entry-field="name"] textarea').count()==0,'Test name starts as read-only catalog content')
            p.locator('[data-edit-field="name"]').click();p.locator('#edit-name').fill('Intentional sample name')
            check(save_button(p).inner_text()=='Save','Editing a normal catalog entry uses Save, not a stray review-queue navigation')
    if ONLY in [None,'blocked-and-capabilities']:
        with case('blocked-and-capabilities') as p:
            check(p.evaluate('stageCounts().review')==45,'Editor To review count excludes the unmapped test and deferred test')
            check(p.locator('[data-all-filter="waiting"]').inner_text()=='1 test waiting on a lab name','Editor sees a quiet link for administrator-only work')
            open_test(p,'786513')
            check(p.locator('.blocker').is_visible() and 'KH CHEMISTRY' in p.locator('.blocker').inner_text(),'Blocked test gives a plain lab-name explanation')
            check(p.locator('[data-answer]').count()==0,'A blocked test does not pretend it has an answer card the editor can use')
            p.locator('[data-request="786513"]').click();p.get_by_role('button',name='Note request',exact=True).click()
            check('No message was sent' in p.locator('#toast').inner_text(),'Request-help placeholder clearly identifies its limits')
            open_test(p,'785258')
            check(p.locator('[data-write="labs"]').count()==0,'Performing laboratories never offer a nonfunctional Write my own')
            p.locator('#role').select_option('admin');p.locator('[data-nav="worklist"]').click()
            check(p.locator('.list-section').first.locator('h2').inner_text().startswith('Waiting on a lab name'),'Administrators see waiting lab-name work first')
            p.locator('[data-test="786513"]').first.click();p.locator('[data-blocker="786513"]').click()
            p.locator('#map-name').fill('Chemistry Laboratory KOP Hospital');p.locator('[data-action="save-mapping"]').click()
            check(p.evaluate("!byId('786513').blocked && needsReview(byId('786513')) && byId('786513').approval===null"),'Saving a lab name enables review without combining it with approval')
            p.locator('[data-action="mapping-back"]').click()
            check(p.locator('h1').inner_text()=='Basic Metabolic Panel','Lab-name task provides a direct return to the test')
    if ONLY in [None,'search-back-and-mobile']:
        with case('search-back-and-mobile') as p:
            p.locator('#search').fill('Ferritin')
            check(p.locator('[data-test="demo-ferritin"]').first.is_visible(),'Search finds tests outside the selected worklist tab')
            check('1 result across all tests' in p.locator('.list-controls').inner_text(),'Search uses correct singular result wording')
            check(p.locator('.tab[aria-pressed="true"]').count()==0,'No status tab falsely remains active during global search')
            p.locator('#search').fill('');p.locator('[data-select="demo-tsh|name"]').check();p.locator('[data-test="demo-tsh"]').first.click();p.locator('[data-action="back-worklist"]').click()
            check(p.locator('[data-select="demo-tsh|name"]').is_checked(),'Worklist selection survives opening a test and returning')
            open_test(p,'demo-tsh');url=p.url;p.reload();check(p.url==url and p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','A test URL survives refresh')
            p.locator('[data-nav="downloads"]').click();p.go_back();check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Browser Back stays inside the app')
        with case('search-back-and-mobile',{'width':390,'height':844}) as p:
            check(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Phone worklist does not require sideways scrolling')
            p.locator('#role').select_option('admin');p.locator('#role').select_option('editor')
            check(p.locator('#role').input_value()=='editor','One phone role selector works both ways')
            check(p.locator('[data-action="reset"]').is_visible(),'Phone reset is available in the sample-data strip')
            open_test(p,'demo-tsh')
            check(p.locator('table').count()==0 and p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Phone choice cards stack without a scrolling table')
            check(p.locator('.answer-card').first.bounding_box()['height']>=44,'Phone decision targets exceed 44px')
            p.screenshot(path=str(ROOT/'review-assets'/'v6-mobile.png'),full_page=True)
    if ONLY in [None,'screen-rules-and-focus']:
        with case('screen-rules-and-focus') as p:
            check(p.locator('.test-row,.change-row').first.bounding_box()['y']<450,'First change is visible well above the previous 562px starting point')
            check(p.locator('.tab').count()==4,'Only the four requested worklist tabs are present')
            check(p.locator('.rail,.stats,[data-action="group"]').count()==0,'Sidebar, repeated tiles, and separate group-review action are removed')
            check(p.locator('#role').count()==1,'There is one demo role control')
            check(p.locator('body').evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')==15,'Body text uses the requested 15px size')
            check(p.locator('small').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=13,'Small visible labels meet the 13px minimum')
            check(p.locator('button.primary:disabled').count()==0,'No disabled main action is shown')
            p.locator('[data-inline="demo-tsh|name|epic"]').click()
            check(p.locator('[data-inline="demo-tsh|name|epic"]').evaluate('n=>n===document.activeElement'),'Inline choice retains keyboard focus')
            check(p.locator('button.primary').count()==1,'Unsaved choices have exactly one main action')
            p.locator('[data-select="demo-crp|name"]').check()
            check(p.locator('button.primary').count()==1,'Selecting more rows does not create two competing main actions')
            p.locator('[data-action="clear-selection"]').click();p.locator('[data-action="see-changes"]').click();p.get_by_role('button',name='Continue choosing',exact=True).click()
            check(p.locator('[data-action="see-changes"]').evaluate('n=>n===document.activeElement'),'Dialog returns focus to See changes')
            check(p.locator('[role="status"]').count()==1,'One live feedback region avoids repeated per-chip announcements')
    if ONLY in [None,'multiple-questions-and-validation']:
        with case('multiple-questions-and-validation') as p:
            p.evaluate("applySource('Epic',{'785258':{name:'New CBC display name'}});render();")
            open_test(p,'785258');check(p.locator('.question').count()==2,'Two open changes are presented together on one test')
            p.locator('[data-action="defer-rest"]').click();save_button(p).click()
            check(p.evaluate("!toReview(byId('785258')) && deferred(byId('785258'))"),'Decide later sets the whole test aside even when another change is waiting')
            p.evaluate("applySource('Epic',{'785258':{labs:'Another changed laboratory'}});refreshWorking();render();")
            check(p.evaluate("toReview(byId('785258')) && !deferred(byId('785258'))"),'A new Epic change reopens a test that was set aside for a different question')
            open_test(p,'demo-tsh');p.locator('[data-write="name"]').click();p.locator('#edit-name').fill('')
            p.keyboard.press('Control+s')
            check(p.evaluate("!byId('demo-tsh').decisions.name && dirtyNow()"),'An empty required name cannot be saved into an unreachable approval state')
            check('before saving' in p.locator('#toast').inner_text(),'Invalid save explains what to enter without a disabled primary button')
    if ONLY in [None,'bulk-keep-and-later']:
        with case('bulk-keep-and-later') as p:
            p.locator('[data-select-section="name"]').click()
            check(p.locator('[data-action="bulk-olsd"]').inner_text()=='Keep what is in the OLSD','Bulk keep uses the requested OLSD wording')
            check(p.locator('[data-action="bulk-defer"]').is_visible(),'Bulk selection offers Decide later alongside Epic and Keep')
            p.locator('[data-action="bulk-olsd"]').click()
            check(p.evaluate("unsavedIds().length===32 && !byId('demo-tsh').decisions.name"),'Bulk keep stages every selected choice without saving')
            save_button(p).click()
            check(p.evaluate("state.tests.filter(t=>t.decisions.name?.choice==='olsd').length")==32,'Save records all 32 deliberate keeps')
            check(p.evaluate('state.tests.filter(canApprove).length')==0,'Bulk keeps that change nothing require no approval')
        with case('bulk-keep-and-later') as p:
            p.locator('[data-select-section="labs"]').click();p.locator('[data-action="bulk-defer"]').click()
            check(p.evaluate("unsavedIds().length===11 && !byId('785258').decisions.labs"),'Bulk Decide later remains unsaved until Save')
            check('Decide later' in p.locator('[data-row="785258|labs"]').inner_text(),'Unsaved rows identify the chosen bulk outcome')
            save_button(p).click()
            check(p.evaluate('stageCounts().review')==34,'Saved bulk deferral removes all 11 lab changes from To review')
            check(p.evaluate('state.tests.filter(deferred).length')==12,'Bulk deferred tests remain findable with the existing set-aside record')
            check(p.evaluate('state.tests.filter(canApprove).length')==0,'Deferring a batch never approves it')
    if ONLY in [None,'save-stay-next-exit']:
        with case('save-stay-next-exit') as p:
            open_test(p,'demo-tsh');choose(p,'name','epic')
            check(p.locator('[data-action="save"]').is_visible() and p.locator('[data-action="save-next"]').is_visible() and p.locator('[data-action="save-exit"]').is_visible(),'Review page offers Save, Save and next, and Save and exit separately')
            url=p.url;p.locator('[data-action="save"]').click()
            check(p.url==url and p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Save stays on the same test')
            check(p.evaluate("byId('demo-tsh').decisions.name.choice==='epic' && byId('demo-tsh').approval===null"),'Save persists the choice without approving it')
            open_test(p,'demo-crp');choose(p,'name','epic');p.locator('[data-action="save-exit"]').click()
            check(p.locator('h1').inner_text()=='Catalog worklist','Save and exit returns to the worklist')
            check(p.evaluate("byId('demo-crp').decisions.name.choice==='epic' && !dirtyNow()"),'Save and exit preserves the choice and clears only unsaved work')
        with case('save-stay-next-exit') as p:
            open_test(p,'demo-tsh');p.locator('[data-write="name"]').click();p.locator('#edit-name').fill('');url=p.url
            p.locator('[data-action="save-exit"]').click()
            check(p.url==url and p.evaluate('dirtyNow()'),'Failed validation cannot exit the editor without saving')
            check('before saving' in p.locator('#toast').inner_text(),'Save and exit explains an invalid value instead of navigating away')
            p.get_by_role('link',name='OLSD Catalog manager',exact=True).click();p.get_by_role('dialog').get_by_role('button',name='Save and continue',exact=True).click()
            check(p.url==url and p.evaluate('dirtyNow()'),'Invalid Save and continue also stays in the editor')
    if ONLY in [None,'previous-and-home']:
        with case('previous-and-home') as p:
            open_test(p,'785258')
            check(p.get_by_role('button',name='Previous test',exact=True).is_disabled(),'First test shows a clear unavailable Previous control')
            choose(p,'labs','epic');p.locator('[data-action="save-next"]').click()
            check(p.get_by_role('button',name='Previous test',exact=True).is_enabled(),'Previous remains available after the prior test has been saved')
            p.get_by_role('button',name='Previous test',exact=True).click()
            check(p.locator('h1').inner_text()=='CBC, Platelet, No Differential','Previous returns to the saved test, not only undecided tests')
            p.get_by_role('button',name='Next test',exact=True).click()
            check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Next returns to the same review sequence')
            check(p.locator('[data-answer="name:olsd"] strong').inner_text().startswith('Keep what is in the OLSD'),'Individual keep card uses the requested wording')
            choose(p,'name','epic');p.get_by_role('link',name='OLSD Catalog manager',exact=True).click()
            check(p.get_by_role('dialog').is_visible(),'Brand navigation warns about unsaved choices')
            p.get_by_role('button',name='Stay',exact=True).click()
            check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Stay cancels brand navigation and preserves the editor')
            check(p.locator('[data-home]').evaluate('n=>n===document.activeElement'),'Canceling home navigation restores focus to the brand link')
            p.get_by_role('link',name='OLSD Catalog manager',exact=True).click();p.get_by_role('dialog').get_by_role('button',name='Discard',exact=True).click()
            check(p.locator('h1').inner_text()=='Catalog worklist','Clickable brand returns to the main worklist')
            check(p.evaluate("!byId('demo-tsh').decisions.name"),'Discard through the home link does not save a choice')
    if ONLY in [None,'approval-selection-actions']:
        with case('approval-selection-actions') as p:
            for id in ['demo-tsh','demo-crp']:p.locator(f'[data-inline="{id}|name|epic"]').click()
            save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click()
            check(p.locator('[data-approve-select]:checked').count()==0,'Approval checkboxes start unticked')
            check(p.locator('[data-action="approve-all"]').count()==0,'Bulk approval is unavailable until a selection is made')
            p.locator('[data-approve-select="demo-tsh"]').check()
            check(p.locator('[data-action="approve-all"]').inner_text()=='Approve 1 selected test','Bulk approval names only the selected subset')
            p.locator('[data-action="approve-all"]').click()
            check(p.evaluate("approved(byId('demo-tsh')) && byId('demo-crp').approval===null"),'Approving a subset leaves unchecked tests unapproved')
            p.locator('[data-approve-select="demo-crp"]').check();p.locator('[data-action="send-back-selected"]').click()
            check(p.evaluate("needsReview(byId('demo-crp')) && approved(byId('demo-tsh'))"),'Sending back a subset preserves other tests’ approvals')
        with case('approval-selection-actions') as p:
            for id in ['demo-tsh','demo-crp']:p.locator(f'[data-inline="{id}|name|epic"]').click()
            save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click();p.locator('[data-action="select-all-approvals"]').click()
            check(p.locator('[data-approve-select]:checked').count()==2,'Approval Select all checks the full list')
            check(p.locator('[data-action="send-back-selected"]').inner_text()=='Send all 2 back to review','Selected-all action clearly says all tests will return to review')
            p.locator('[data-action="send-back-selected"]').click()
            check(p.evaluate("needsReview(byId('demo-tsh')) && needsReview(byId('demo-crp'))"),'Send all back returns both saved updates to review')
    if ONLY in [None,'download-selection-actions']:
        with case('download-selection-actions') as p:
            for id in ['demo-tsh','demo-crp']:p.locator(f'[data-inline="{id}|name|epic"]').click()
            save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click();p.locator('[data-action="select-all-approvals"]').click();p.locator('[data-action="approve-all"]').click();p.locator('[data-tab="download"]').click()
            check(p.locator('[data-download-select]:checked').count()==0,'Download checkboxes start unticked')
            check(p.locator('[data-download-ids]').count()==0,'Download does not silently include the whole list')
            p.locator('[data-download-select="demo-tsh"]').check();click_download(p,'tested-selected-only.xlsx')
            check(p.evaluate("state.exports.length===1 && state.exports[0].tests.length===1 && state.exports[0].tests[0].id==='demo-tsh'"),'Download contains only the selected test')
            check(p.evaluate("ready(byId('demo-crp')) && ready(byId('785260'))"),'Unchecked tests stay approved and waiting to download')
            p.locator('[data-download-select="demo-crp"]').check();p.locator('[data-action="withdraw-selected"]').click()
            check(p.evaluate("byId('demo-crp').approval===null && approved(byId('785260'))"),'Withdrawing a subset preserves the unchecked approval')
            check(p.evaluate("canApprove(byId('demo-crp'))"),'Withdrawal returns the saved choice to To approve')
        with case('download-selection-actions') as p:
            p.locator('[data-tab="download"]').click();p.locator('[data-action="select-all-downloads"]').click()
            check(p.locator('[data-download-select]:checked').count()==1,'Download Select all checks every ready test')
            check(p.locator('[data-action="withdraw-selected"]').inner_text()=='Withdraw approval for selected test','Selected-all withdrawal labels its exact scope')
            p.locator('[data-action="withdraw-selected"]').click()
            check(p.evaluate("byId('785260').approval===null && state.exports.length===0"),'Withdraw all removes approval without creating a download')
    if ONLY in [None,'one-row-per-test']:
        with case('one-row-per-test') as p:
            check(p.evaluate('state.tests.length')==308,'Sample catalog contains 308 tests')
            check(p.evaluate('stageCounts()')=={'review':45,'approve':0,'download':1,'all':308},'Worklist totals count tests, not the number of changed fields')
            counts=p.locator('.list-section h2').evaluate_all(r"ns=>ns.map(n=>Number(n.textContent.match(/\((\d+)\)/)[1]))")
            check(sum(counts)==45,'Section counts add up to the To review tab count')
            groups=p.locator('[data-change-group]').evaluate_all('ns=>ns.map(n=>n.dataset.changeGroup)')
            check(groups==['multi','name','labs'],'Multiple-change tests precede single-name and single-lab groups')
            for id in ['demo-vitd','demo-a1c']:
                check(p.locator(f'[data-test-row="{id}"]').count()==1,'Multi-change sample '+id+' has exactly one worklist row')
                check(p.locator(f'[data-change-group="multi"] [data-row^="{id}|"]').count()==2,'Both changed fields appear inside '+id+' row')
                check(p.locator(f'[data-change-group="name"] [data-row^="{id}|"], [data-change-group="labs"] [data-row^="{id}|"]').count()==0,'Multi-change sample '+id+' is absent from single-field groups')
            check('Name changes (32)' in p.locator('[data-change-group="name"] h2').inner_text(),'Single-name section excludes the two multi-change tests')
            check('Lab changes (11)' in p.locator('[data-change-group="labs"] h2').inner_text(),'Single-lab section excludes the two multi-change tests')
            p.locator('[data-action="load-more"]').click()
            ids=p.locator('article.test-row,article.change-row').evaluate_all("ns=>ns.map(n=>n.dataset.testRow||n.dataset.row.split('|')[0])")
            check(len(ids)==45 and len(set(ids))==45,'Every loaded test has exactly one row across all review sections')
            p.locator('#search').fill('Vitamin D')
            check(p.locator('.catalog-row').count()==1,'Global search returns a multi-change test only once')
            p.locator('[data-test="demo-vitd"]').first.click()
            check(p.locator('.question').count()==2,'Opening a search result shows both outstanding fields together')
    if ONLY in [None,'multi-selection-and-bulk']:
        with case('multi-selection-and-bulk') as p:
            p.locator('[data-select-test="demo-vitd"]').check()
            check(p.evaluate('[...ui.selected].sort()')==['demo-vitd|labs','demo-vitd|name'],'A test checkbox selects both eligible fields on that test')
            check(p.locator('[data-action="bulk-epic"]').inner_text()=='Use Epic for 2 changes on 1 test','Bulk action states both field and test counts')
            p.locator('[data-select-section="multi"]').click()
            check(p.evaluate('ui.selected.size')==4 and p.locator('[data-select-test]:checked').count()==2,'Section Select all includes both changes on both tests')
            p.locator('[data-select-section="multi"]').click()
            check(p.evaluate('ui.selected.size')==0,'Section Clear selection removes every selected field')
            p.locator('[data-select-section="multi"]').click();p.locator('[data-action="bulk-epic"]').click()
            check(p.evaluate('unsavedIds().length')==2 and p.evaluate('state.tests.filter(canApprove).length')==0,'Bulk choices stage two tests without approving or saving')
            check(p.locator('[data-test-row="demo-vitd"] [data-row]').count()==2,'Staged changes remain together until Save')
            save_button(p).click()
            check(p.evaluate("['demo-vitd','demo-a1c'].every(id=>canApprove(byId(id)) && ['name','labs'].every(k=>byId(id).decisions[k].choice==='epic'))"),'One Save records all four explicit choices')
            check(p.evaluate('stageCounts().review')==43,'Saving two complete tests removes exactly two from To review')
            p.locator('[data-action="undo-save"]').click()
            check(p.evaluate("['demo-vitd','demo-a1c'].every(id=>pendingKeys(byId(id)).length===2 && !canApprove(byId(id)))"),'Undo restores both unresolved fields on both tests')
        for outcome in ['olsd','defer']:
            with case('multi-selection-and-bulk') as p:
                p.locator('[data-select-test="demo-vitd"]').check();p.locator(f'[data-action="bulk-{outcome}"]').click()
                check(p.evaluate("pendingKeys(byId('demo-vitd')).length")==2,'Bulk '+outcome+' leaves saved decisions untouched until Save')
                save_button(p).click()
                check(p.evaluate("!canApprove(byId('demo-vitd')) && !ready(byId('demo-vitd'))"),'Bulk '+outcome+' never creates an exportable change')
                check(p.evaluate("retained(byId('demo-vitd'))" if outcome=='olsd' else "deferred(byId('demo-vitd'))"),'Bulk '+outcome+' remains discoverable after Save')
    if ONLY in [None,'multi-free-text-safety']:
        with case('multi-free-text-safety') as p:
            p.evaluate("applySnapshot({'demo-vitd':{conditions:'New OLSD conditions requiring review'}});render();")
            check(p.locator('[data-test-row="demo-vitd"] [data-row]').count()==3,'A third free-text change stays in the same test row')
            check(p.locator('[data-test-row="demo-vitd"] [data-inline*="conditions"]').count()==0,'Free text never gains a bulk Epic acceptance action')
            p.locator('[data-select-test="demo-vitd"]').check()
            check(p.evaluate('ui.selected.size')==2,'Test selection includes only eligible name and laboratory changes')
            p.locator('[data-action="bulk-epic"]').click();save_button(p).click()
            check(p.evaluate("!!byId('demo-vitd').pending.conditions && !byId('demo-vitd').decisions.conditions && !canApprove(byId('demo-vitd'))"),'Bulk save leaves the free-text question open and approval unavailable')
            p.locator('[data-test="demo-vitd"]').first.click()
            check(p.locator('[data-question="conditions"]').is_visible(),'Remaining free-text question stays accessible for individual review')
    if ONLY in [None,'multi-partial-save-and-export']:
        with case('multi-partial-save-and-export') as p:
            p.locator('[data-action="walk"]').click()
            check(p.locator('h1').inner_text()=='Vitamin D, 25-Hydroxy','Full walkthrough starts at the first displayed multi-change test')
            check(p.locator('.question').count()==2 and '0 of 2 chosen' in p.locator('.question-count').inner_text(),'Both questions show a clear initial decision count')
            choose(p,'name','epic')
            p.locator('[data-action="see-changes"]').click();p.get_by_role('button',name='Continue choosing',exact=True).click()
            check(p.locator('.question').count()==2 and '1 of 2 chosen' in p.locator('.question-count').inner_text(),'First choice stays visible alongside the unresolved field')
            check('1 more to choose on this test' in p.locator('.save-bar').inner_text(),'Partial choice identifies the remaining review work')
            check(p.locator('[data-action="save-next"]').count()==0,'Save and next is withheld while another field needs a choice')
            save_button(p).click()
            check(p.locator('h1').inner_text()=='Vitamin D, 25-Hydroxy' and p.evaluate("toReview(byId('demo-vitd')) && !canApprove(byId('demo-vitd'))"),'Partial Save stays on the test and keeps it in To review')
            p.locator('[data-action="back-worklist"]').click()
            check(p.locator('[data-change-group="labs"] [data-row="demo-vitd|labs"]').is_visible() and p.locator('[data-test-row="demo-vitd"]').count()==0,'Partial Save moves the test to its one remaining change section')
            p.locator('[data-test="demo-vitd"]').first.click()
            p.reload();check(p.evaluate("byId('demo-vitd').decisions.name.choice==='epic' && !!byId('demo-vitd').pending.labs"),'Partial Save survives refresh without deciding the remaining field')
            choose(p,'labs','epic');p.locator('[data-action="save"]').click()
            check(p.evaluate("canApprove(byId('demo-vitd'))") and p.locator('.saved-change').count()==2,'Approval becomes available only after both choices are saved')
            approve_one(p,'demo-vitd');wb=click_download(p,'tested-v7-multi-field.xlsx');rows=list(wb['Tests'].values);row=dict(zip(rows[0],rows[1]))
            check(row['Test Name']=='Vitamin D 25-OH, Total','Multi-field workbook contains the explicitly accepted Epic name')
            check('Chemistry Laboratory KOP' in str(row.get('Performing Lab','')),'Multi-field workbook contains the explicitly accepted laboratory')
    if ONLY in [None,'selected-walkthrough-order']:
        with case('selected-walkthrough-order') as p:
            p.locator('[data-select-test="demo-a1c"]').check();p.locator('[data-select="demo-tsh|name"]').check()
            p.locator('.selection-bar [data-action="walk"]').click()
            check(p.evaluate('ui.queue')==['demo-a1c','demo-tsh'],'Selected walkthrough has one entry per test in displayed worklist order')
            check(p.locator('h1').inner_text()=='Hemoglobin A1c','Selected walkthrough opens its first displayed test')
            choose(p,'name','epic');choose(p,'labs','olsd');p.locator('[data-action="save-next"]').click()
            check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone','Save and next follows the selected sequence after both decisions')
            p.get_by_role('button',name='Previous test',exact=True).click()
            check(p.locator('h1').inner_text()=='Hemoglobin A1c','Previous revisits a completed test in the selected sequence')
            check(p.evaluate("byId('demo-vitd').decisions.name===undefined && byId('demo-vitd').decisions.labs===undefined"),'Walkthrough never modifies an unselected test')
    if ONLY in [None,'multi-defer-remaining']:
        with case('multi-defer-remaining') as p:
            open_test(p,'demo-vitd');choose(p,'name','epic');p.locator('[data-action="defer-rest"]').click()
            check(p.evaluate("staged.get('demo-vitd').decisions.name.choice==='epic' && staged.get('demo-vitd').decisions.labs.choice==='defer'"),'Decide later preserves a chosen field and defers only the unanswered field')
            check(p.evaluate("!byId('demo-vitd').decisions.name"),'Deferring remaining questions is unsaved until Save')
            save_button(p).click()
            check(p.evaluate("deferred(byId('demo-vitd')) && !toReview(byId('demo-vitd')) && !canApprove(byId('demo-vitd'))"),'Saving remaining deferral sets the test aside without approval')
            p.locator('[data-set-aside="labs"] [data-change-choice]').click()
            check(p.locator('[data-question="labs"]').is_visible() and p.evaluate("byId('demo-vitd').decisions.name.choice==='epic'"),'Decide now reopens the remaining field and preserves the earlier choice')
            choose(p,'labs','epic');save_button(p).click()
            check(p.evaluate("canApprove(byId('demo-vitd'))"),'Deciding the remaining field returns the set-aside update to approval')
    if ONLY in [None,'multi-keyboard-and-mobile']:
        with case('multi-keyboard-and-mobile') as p:
            open_test(p,'demo-vitd');p.keyboard.press('1')
            check(p.evaluate("staged.get('demo-vitd').decisions.name.choice==='epic' && !staged.get('demo-vitd').decisions.labs"),'Shortcut 1 decides only the first unanswered field')
            check(p.locator('[data-question="name"] .shortcut').count()==0 and p.locator('[data-question="labs"] .shortcut').count()==2,'Shortcut hints follow only the first unanswered change')
            p.keyboard.press('2')
            check(p.evaluate("staged.get('demo-vitd').decisions.labs.choice==='olsd'"),'Shortcut 2 moves to the next unanswered field')
            check(p.locator('.question .shortcut').count()==0,'Shortcut hints disappear when every multi-change question has a choice')
            p.keyboard.press('1')
            check(p.evaluate("staged.get('demo-vitd').decisions.labs.choice==='olsd'"),'Extra numeric keys do not alter a completed multi-change review')
            check(p.locator('.question').count()==2,'Keyboard decisions keep both fields visible before Save')
        with case('multi-keyboard-and-mobile',{'width':390,'height':844}) as p:
            check(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Multi-change worklist fits a phone without horizontal scrolling')
            line=p.locator('[data-row="demo-vitd|name"]')
            label_box=line.locator('.line-label').bounding_box();value_box=line.locator('.line-value').bounding_box()
            check(label_box['y']+label_box['height']<=value_box['y'],'Phone field labels stack above their values')
            p.locator('[data-select-test="demo-vitd"]').check()
            check(p.locator('[data-select-test="demo-vitd"]').evaluate('n=>n===document.activeElement'),'Test selection retains keyboard focus')
            p.locator('[data-select-test="demo-vitd"]').uncheck();p.locator('[data-test="demo-vitd"]').first.click()
            check(p.locator('.question').count()==2 and p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Both multi-change questions fit on a phone')
            choose(p,'name','epic');choose(p,'labs','olsd')
            p.locator('[data-action="save-more"]').click()
            check(p.locator('[data-action="save"]').is_visible() and p.locator('[data-action="save-exit"]').is_visible(),'Phone keeps Save and Save and exit available under More for multi-change tests')
            p.screenshot(path=str(ROOT/'review-assets'/'v7-multi-mobile.png'),full_page=True)
    if ONLY in [None,'screen-order-and-other-fields']:
        with case('screen-order-and-other-fields') as p:
            p.locator('[data-action="walk"]').click()
            p.get_by_role('button',name='Next test',exact=True).click()
            check(p.locator('h1').inner_text()=='Hemoglobin A1c','Next follows the second test displayed in the multi-change section')
            p.get_by_role('button',name='Next test',exact=True).click()
            check(p.locator('h1').inner_text()=='Thyroid Stimulating Hormone' and '3 of 45' in p.locator('.test-nav').inner_text(),'Next crosses into the name section in screen order with the correct position')
            p.get_by_role('button',name='Previous test',exact=True).click()
            check(p.locator('h1').inner_text()=='Hemoglobin A1c','Previous reverses the displayed test order')
        with case('screen-order-and-other-fields') as p:
            p.evaluate("applySnapshot({'demo-vitd':{categories:'Changed categories'},'785260':{conditions:'New observed conditions'}});render();")
            check('Open this test to review the change.' in p.locator('[data-row="demo-vitd|categories"]').inner_text(),'A non-name/lab field uses the individual-review prompt even when Epic has a value')
            check('Unsaved' not in p.locator('[data-test-row="demo-vitd"]').inner_text(),'Untouched multi-change lines are not marked Unsaved')
            p.locator('[data-inline="demo-vitd|name|epic"]').click()
            check('Unsaved' in p.locator('[data-row="demo-vitd|name"]').inner_text() and 'Unsaved' not in p.locator('[data-row="demo-vitd|labs"]').inner_text(),'Only the line with a new choice is marked Unsaved')
            p.locator('[data-action="discard"]').click()
            check('Unacceptable conditions' in p.locator('[data-change-group="other"] [data-test-row="785260"]').inner_text(),'An Other changes row names its outstanding field')
            p.locator('[data-select-test="785260"]').check()
            check(p.locator('.selection-bar [data-action="walk"]').is_visible() and p.locator('[data-action="bulk-epic"]').count()==0,'A free-text-only test can be selected for walkthrough without bulk acceptance')
            p.locator('.selection-bar [data-action="walk"]').click()
            check(p.evaluate('ui.queue')==['785260'] and p.locator('[data-question="conditions"]').is_visible(),'Selected free-text test opens individually for review')
    if ONLY in [None,'next-1-change-saved-choice']:
        with case('next-1-change-saved-choice') as p:
            open_test(p,'785258');choose(p,'labs','olsd');save_button(p).click();p.reload()
            check('Kept' in p.locator('[data-saved-choice="labs"]').inner_text(),'1: saved lab keep remains visible after refresh without Undo')
            p.locator('[data-change-choice="labs"]').click()
            check(p.locator('[data-answer="labs:epic"]').is_visible() and not p.evaluate('dirtyNow()'),'1: Change reopens lab cards without changing saved data')
            check(p.locator('[data-answer="labs:epic"]').evaluate('n=>n===document.activeElement'),'1: Change moves keyboard focus into the reopened answer cards')
            choose(p,'labs','epic');check(p.evaluate("byId('785258').decisions.labs.choice==='olsd'"),'1: new saved-choice selection is not persisted before Save')
            save_button(p).click();approve_one(p,'785258')
            check(p.locator('[data-withdraw="785258"]').is_visible(),'1: approved test offers Withdraw approval on its test page')
            p.locator('[data-change-choice="labs"]').click()
            check('withdraw' in p.locator('.approval-warning').inner_text() and p.evaluate("approved(byId('785258'))"),'1: reopening an approved choice warns but preserves approval')
            choose(p,'labs','olsd');save_button(p).click()
            check(p.evaluate("!approved(byId('785258')) && byId('785258').decisions.labs.choice==='olsd'"),'1: saving a changed choice withdraws approval')
            p.locator('[data-change-choice="labs"]').click();choose(p,'labs','epic');save_button(p).click()
            check(p.locator('[data-send-back="785258"]').count()==0,'1: saved update has no overlapping Send back action on the test page')
            p.goto(BASE+'/#/worklist?tab=approve');p.locator('[data-send-back="785258"]').click();check(p.evaluate("toReview(byId('785258'))"),'1: approval-list Send back reopens the saved update')
    if ONLY in [None,'next-2-partial-and-deferred-choices']:
        with case('next-2-partial-and-deferred-choices') as p:
            open_test(p,'demo-a1c');choose(p,'name','epic');p.locator('[data-action="save"]').click()
            check('Hemoglobin A1c, Whole Blood' in p.locator('[data-saved-choice="name"]').inner_text(),'2a: partly finished test displays its saved proposed name')
            check(p.locator('[data-saved-choice="name"] .current-olsd').inner_text()=='Hemoglobin A1c','2a: catalog entry displays OLSD name, not the saved proposal')
            check(p.locator('[data-question="labs"]').is_visible(),'2a: remaining lab question stays visible beside saved choices')
        with case('next-2-partial-and-deferred-choices') as p:
            open_test(p,'demo-vitd');choose(p,'name','epic');p.locator('[data-action="defer-rest"]').click();save_button(p).click();p.reload()
            check('Vitamin D 25-OH, Total' in p.locator('[data-saved-choice="name"]').inner_text(),'2b: accepted name remains visible on a set-aside test')
            check('Performing laboratories' in p.locator('[data-set-aside="labs"]').inner_text() and 'Chemistry Laboratory KOP' in p.locator('[data-set-aside="labs"]').inner_text(),'2b: Set aside names the field and shows its Epic value')
            check(p.locator('[data-set-aside="labs"] .current-olsd').inner_text()=='Chemistry Laboratory Main Hospital','2b: set-aside catalog entry still shows actual OLSD laboratories')
    if ONLY in [None,'next-3-sent-back-wording']:
        with case('next-3-sent-back-wording') as p:
            open_test(p,'demo-tsh');p.locator('[data-write="name"]').click();p.locator('#edit-name').fill('TSH wording to retain');save_button(p).click()
            p.goto(BASE+'/#/worklist?tab=approve');p.locator('[data-send-back="demo-tsh"]').click();p.reload();open_test(p,'demo-tsh')
            check('TSH wording to retain' in p.locator('[data-answer="name:saved"]').inner_text(),'3: sent-back custom wording survives reload in a third answer card')
            p.locator('[data-action="back-worklist"]').click();p.locator('[data-tab="review"]').click()
            row=p.locator('[data-test-row="demo-tsh"]')
            check('TSH wording to retain' in row.inner_text() and row.locator('[data-inline]').count()==0,'3: sent-back row displays saved wording and requires opening the test')
            row.locator('[data-test="demo-tsh"]').first.click();choose(p,'name','saved');save_button(p).click()
            check(p.evaluate("byId('demo-tsh').proposed.name==='TSH wording to retain' && canApprove(byId('demo-tsh'))"),'3: Keep my saved wording restores the proposal for separate approval')
    if ONLY in [None,'next-4-approval-walk']:
        with case('next-4-approval-walk') as p:
            for id in ['demo-tsh','demo-crp']:p.locator(f'[data-inline="{id}|name|epic"]').click()
            save_button(p).click();p.get_by_role('button',name='Go to approvals',exact=True).click()
            p.locator('[data-action="walk"]').click()
            check(p.locator('[data-action="approve-next"]').inner_text()=='Approve and next','4: approval list offers a walkthrough with Approve and next')
            p.locator('[data-action="approve-next"]').click()
            check(p.locator('h1').inner_text()=='C-Reactive Protein' and p.locator('[data-download-ids]').count()==0,'4: approval moves to next test without offering a single-test download')
            p.locator('[data-action="approve-next"]').click()
            check(p.locator('h1').inner_text()=='Catalog worklist' and '2 tests approved' in p.locator('.walk-result').inner_text(),'4: final approval ends the walk and returns to the list')
            check(p.get_by_role('button',name='Go to downloads',exact=True).is_visible() and p.evaluate('state.exports.length')==0,'4: completion offers To download and never creates per-test files')
    if ONLY in [None,'next-5-review-walk-ending']:
        with case('next-5-review-walk-ending') as p:
            p.locator('[data-select="demo-tsh|name"]').check();p.locator('[data-select="demo-crp|name"]').check();p.locator('.selection-bar [data-action="walk"]').click()
            choose(p,'name','epic');p.locator('[data-action="save-next"]').click();choose(p,'name','epic')
            check(p.locator('[data-action="save-finish"]').inner_text()=='Save and finish','5: last test offers Save and finish')
            p.locator('[data-action="save-finish"]').click()
            check(p.locator('h1').inner_text()=='Catalog worklist' and '2 tests saved' in p.locator('.walk-result').inner_text(),'5: Save and finish returns to the list with a saved-test count')
            check(p.get_by_role('button',name='Go to approvals',exact=True).is_visible() and p.evaluate('state.tests.filter(canApprove).length')==2,'5: completion points to separate approval without approving')
        with case('next-5-review-walk-ending') as p:
            p.locator('[data-select-section="multi"]').click();p.locator('.selection-bar [data-action="walk"]').click()
            choose(p,'name','epic');p.get_by_role('button',name='Next test',exact=True).click()
            p.get_by_role('dialog').get_by_role('button',name='Save and continue',exact=True).click()
            check(p.evaluate("!!byId('demo-vitd').pending.labs && byId('demo-vitd').decisions.name.choice==='epic'"),'5: Next arrow can save a partial decision without resolving its other field')
            choose(p,'name','epic');choose(p,'labs','olsd');p.locator('[data-action="save-finish"]').click()
            check('2 tests saved' in p.locator('.walk-result').inner_text(),'5: finished saved count includes choices saved through the navigation prompt')
            check(p.evaluate("toReview(byId('demo-vitd')) && canApprove(byId('demo-a1c'))"),'5: finish preserves partial work in review and completed work in approval')
    if ONLY in [None,'next-6-back-link-context']:
        for tab,id,name in [('all','demo-tsh','All tests'),('download','785260','To download')]:
            with case('next-6-back-link-context') as p:
                p.locator(f'[data-tab="{tab}"]').click();p.locator(f'[data-test="{id}"]').first.click()
                check(name in p.locator('[data-action="back-worklist"]').inner_text(),'6: back link names '+name)
                p.reload();check(name in p.locator('[data-action="back-worklist"]').inner_text(),'6: list context survives refreshing the test URL')
                check(p.evaluate('ui.queue.length')==(308 if tab=='all' else 1),'6: refreshed test navigation retains the originating list scope')
                p.locator('[data-action="back-worklist"]').click();check(p.locator(f'[data-tab="{tab}"]').get_attribute('aria-pressed')=='true','6: back link returns to '+name)
        with case('next-6-back-link-context') as p:
            p.locator('#search').fill('Ferritin');p.locator('[data-test="demo-ferritin"]').first.click()
            check('Search results' in p.locator('[data-action="back-worklist"]').inner_text(),'6: search opens a test with a Search results back link')
            p.locator('[data-action="back-worklist"]').click();check(p.locator('#search').input_value()=='Ferritin','6: returning preserves the search query')
    if ONLY in [None,'next-7-primary-save']:
        with case('next-7-primary-save') as p:
            p.locator('[data-action="walk"]').click();choose(p,'name','epic');choose(p,'labs','olsd')
            check(p.locator('.save-bar .primary').get_attribute('data-action')=='save-next','7: review walkthrough makes Save and next primary')
            check(p.locator('[data-action="save"]').is_visible(),'7: review walkthrough retains a separate Save action')
        with case('next-7-primary-save') as p:
            open_test(p,'demo-tsh');choose(p,'name','epic')
            check(p.locator('.save-bar .primary').get_attribute('data-action')=='save','7: ordinary editor keeps Save primary')
    if ONLY in [None,'next-8-16-worklist-and-small-fixes']:
        with case('next-8-16-worklist-and-small-fixes') as p:
            p.locator('[data-select="demo-crp|name"]').check();p.locator('[data-inline="demo-tsh|name|epic"]').click()
            check(p.locator('[data-select="demo-crp|name"]').is_checked(),'8: inline choice preserves other ticked rows')
            check(p.locator('.selection-bar [data-action="save"]').is_visible(),'9: selection bar exposes Save for another unsaved choice')
            p.locator('.selection-bar [data-action="save"]').click()
            check(p.evaluate("byId('demo-tsh').decisions.name.choice==='epic'"),'9: selection-bar Save persists unsaved choices')
            p.locator('summary').filter(has_text='Filter').click();p.locator('#lab-filter').select_option('UC CHEMISTRY')
            check('of 44 tests' in p.locator('.filter-count').inner_text(),'11: filtered worklist shows the visible and total test counts')
            check(p.evaluate("age(new Date(Date.now()-25*3600000).toISOString())")=='1 day old','13: source age uses singular day')
        with case('next-8-16-worklist-and-small-fixes') as p:
            open_test(p,'demo-crp');choose(p,'name','olsd');p.locator('[data-toggle-note="name"]').click();p.locator('#note-name').fill('Use public wording');save_button(p).click()
            p.locator('[data-nav="worklist"]').click();p.locator('[data-tab="all"]').click();p.locator('#all-filter').select_option('kept')
            check('Use public wording' in p.locator('.decision-summary').inner_text() and 'C Reactive Protein' in p.locator('.decision-summary').inner_text(),'10: Kept wording list explains the retained value and note')
            p.locator('#all-filter').select_option('later');check('Waiting for laboratory guidance' in p.locator('.decision-summary').inner_text(),'10: Set aside list names the field and shows its note')
        with case('next-8-16-worklist-and-small-fixes') as p:
            p.evaluate("applySnapshot({'demo-tsh':{conditions:'New conditions'}});render();")
            open_test(p,'demo-tsh')
            check("catalog's unacceptable conditions changed" in p.locator('[data-question="conditions"] h2').inner_text(),'12: OLSD change heading names the field')
            check('Was' in p.locator('.source-context').inner_text() and 'Now' in p.locator('.source-context').inner_text(),'12: OLSD change shows earlier and current values')
            choose(p,'name','epic');p.locator('[data-action="see-changes"]').click()
            check(p.locator('[data-unsaved-field="name"]').inner_text().count('Test name')==1,'14: unsaved comparison names a changed field once')
            p.get_by_role('button',name='Continue choosing',exact=True).click();p.locator('[data-action="discard"]').click();p.locator('[data-action="back-worklist"]').click()
            p.locator('[data-inline="demo-vitd|name|epic"]').click()
            check(p.locator('[data-row="demo-vitd|name"] .line-value').inner_text().count('Use Epic')==0,'15: changed line shows Unsaved without repeating the highlighted choice')
        with case('next-8-16-worklist-and-small-fixes',{'width':390,'height':844}) as p:
            open_test(p,'demo-vitd');choose(p,'name','epic');choose(p,'labs','olsd')
            check(p.locator('.save-bar').bounding_box()['height']<=125 and p.locator('.save-bar .primary').is_visible(),'16: collapsed phone save bar stays compact with its main action visible')
            check(not p.locator('[data-action="save-exit"]').is_visible(),'16: phone secondary actions start behind More')
            p.locator('[data-action="save-more"]').click();check(p.locator('[data-action="save-exit"]').is_visible(),'16: More reveals phone secondary actions')
            p.screenshot(path=str(ROOT/'review-assets'/'next-mobile-save.png'),full_page=True)
    if ONLY in [None,'once-1-consolidated-changes']:
        with case('once-1-consolidated-changes') as p:
            open_test(p,'785258');choose(p,'labs','epic');save_button(p).click()
            check(p.locator('.saved-choices').count()==1 and p.locator('.saved-choices h2').inner_text()=='Ready for approval','1: one saved section shows Ready for approval')
            check(p.locator('[data-saved-choice="labs"]').count()==1 and p.locator('[data-entry-field="labs"]').count()==0,'1: saved lab change appears once and is omitted from Other fields')
            check('In OLSD now' in p.locator('[data-saved-choice="labs"]').inner_text() and 'After import' in p.locator('[data-saved-choice="labs"]').inner_text(),'1: single saved row compares OLSD now with After import')
            check(p.locator('.saved-choices [data-edit-field], [data-send-back]').count()==0 and p.locator('[data-change-choice="labs"]').count()==1,'1: unconfirmed saved row has one Change action and no Edit or Send back')
            approve_one(p,'785258')
            check(p.locator('.saved-choices h2').inner_text()=='Approved' and p.locator('[data-saved-choice="labs"]').count()==1,'1: approval updates the heading without repeating the change')
            check(p.locator('.catalog-entry h2').inner_text()=='Other fields','1: lower section is named Other fields')
        with case('once-1-consolidated-changes') as p:
            open_test(p,'demo-vitd');choose(p,'name','epic');p.locator('[data-action="defer-rest"]').click();save_button(p).click()
            check(p.locator('[data-saved-choice="name"]').count()==1 and p.locator('[data-set-aside="labs"]').count()==1,'1: saved and set-aside fields are each listed once')
            check(p.locator('[data-entry-field="name"], [data-entry-field="labs"]').count()==0,'1: Other fields excludes both saved and set-aside fields')
    if ONLY in [None,'once-2-confirmed-status']:
        with case('once-2-confirmed-status') as p:
            open_test(p,'785260');click_download(p,'tested-confirmed-once.xlsx')
            p.locator('#role').select_option('admin');p.locator('[data-nav="downloads"]').click();p.locator('.admin-comparison > summary').click();p.locator('[data-reconcile$=":match"]').click();open_test(p,'785260')
            check(p.locator('.saved-choices h2').inner_text()=='Confirmed in OLSD' and '2026' in p.locator('.confirmation-date').inner_text(),'2: confirmed test explicitly shows confirmation and its date')
            check(p.locator('[data-confirmed-choice="conditions"]').count()==1 and p.locator('.saved-choices [data-change-choice]').count()==0,'2: confirmed field has no Change button')
            check('Kept' not in p.locator('.saved-choices').inner_text(),'2: confirmed import is not mislabeled Kept')
            p.locator('[data-edit-field="conditions"]').click();p.locator('#edit-conditions').fill('New change after confirmation');save_button(p).click()
            check(p.locator('.saved-choices h2').inner_text()=='Ready for approval' and p.evaluate("byId('785260').proposed.conditions==='New change after confirmation'"),'2: Edit starts a new saved change requiring approval')
    if ONLY in [None,'once-3-cancel-change']:
        with case('once-3-cancel-change') as p:
            open_test(p,'785258');choose(p,'labs','olsd');save_button(p).click();p.locator('[data-change-choice="labs"]').click()
            check(p.locator('[data-saved-choice="labs"]').count()==0 and p.locator('[data-entry-field="labs"]').count()==0,'3: open Change cards replace the saved row instead of duplicating it')
            check(p.locator('[data-question="labs"] h2').inner_text()=='Performing laboratories: what should the catalog say?','3: reopened change uses the short field heading')
            choose(p,'labs','epic');p.locator('[data-cancel-choice="labs"]').click()
            check(p.locator('[data-question="labs"]').count()==0 and not p.evaluate('dirtyNow()') and p.evaluate("byId('785258').decisions.labs.choice==='olsd'"),'3: Cancel closes cards and discards only the unsaved replacement choice')
            p.locator('[data-change-choice="labs"]').click();p.locator('[data-action="back-worklist"]').click();p.locator('#search').fill('CBCND');p.locator('[data-test="785258"]').first.click()
            check(p.locator('[data-question="labs"]').count()==0 and p.locator('[data-saved-choice="labs"]').count()==1,'3: leaving the test closes the reopened cards')
        with case('once-3-cancel-change') as p:
            open_test(p,'demo-a1c');choose(p,'name','epic');save_button(p).click();p.locator('[data-change-choice="name"]').click();choose(p,'name','olsd');choose(p,'labs','epic');p.locator('[data-cancel-choice="name"]').click()
            check(p.evaluate("staged.get('demo-a1c').decisions.labs.choice==='epic' && staged.get('demo-a1c').decisions.name.choice==='epic'"),'3: cancelling one field preserves another field’s unsaved choice')
            save_button(p).click();check(p.evaluate("canApprove(byId('demo-a1c'))"),'3: preserved unsaved choice can still be saved for approval')
    if ONLY in [None,'once-4-no-duplicate-epic-card']:
        with case('once-4-no-duplicate-epic-card') as p:
            open_test(p,'demo-crp');choose(p,'name','epic');save_button(p).click();p.goto(BASE+'/#/worklist?tab=approve');p.locator('[data-send-back="demo-crp"]').click();p.goto(BASE+'/#/worklist?tab=review')
            check(p.locator('[data-inline="demo-crp|name|epic"]').is_visible() and p.locator('[data-inline="demo-crp|name|olsd"]').is_visible(),'4: sent-back Epic wording retains normal inline Epic and Keep buttons')
            p.locator('[data-test="demo-crp"]').first.click()
            check(p.locator('[data-answer="name:saved"]').count()==0 and p.locator('[data-answer="name:epic"]').is_visible(),'4: wording equal to Epic does not create a duplicate third card')
    if ONLY in [None,'once-5-preserve-wording-after-source-change']:
        with case('once-5-preserve-wording-after-source-change') as p:
            open_test(p,'demo-tsh');p.locator('[data-write="name"]').click();p.locator('#edit-name').fill('Our custom public TSH name');save_button(p).click()
            p.evaluate("applySource('OLSD',{'demo-tsh':{name:'New observed OLSD name'}});refreshWorking();render();")
            p.reload()
            check('Our custom public TSH name' in p.locator('[data-answer="name:saved"]').inner_text(),'5: catalog change offers saved wording after a fresh reload')
            note=p.locator('.previous-choice').inner_text()
            check('You saved' in note and 'Epic then' not in note and 'Epic now' not in note,'5: catalog-only change describes the saved choice without claiming Epic changed')
            choose(p,'name','saved');save_button(p).click()
            check(p.evaluate("byId('demo-tsh').proposed.name==='Our custom public TSH name' && canApprove(byId('demo-tsh'))"),'5: retained wording remains a separate saved update for approval')
        with case('once-5-preserve-wording-after-source-change') as p:
            open_test(p,'demo-tsh');choose(p,'name','olsd');save_button(p).click()
            p.evaluate("applySource('Epic',{'demo-tsh':{name:'A genuinely newer Epic name'}});refreshWorking();render();")
            check('Epic then' in p.locator('.previous-choice').inner_text() and 'Epic now' in p.locator('.previous-choice').inner_text(),'5: a real Epic change still shows the earlier and current Epic values')
    if ONLY in [None,'once-6-8-walk-carry-and-wording']:
        with case('once-6-8-walk-carry-and-wording') as p:
            for id in ['demo-tsh','demo-crp','sample-10']:p.locator(f'[data-select="{id}|name"]').check()
            p.locator('.selection-bar [data-action="walk"]').click();choose(p,'name','epic');p.locator('[data-action="save-next"]').click();p.get_by_role('button',name='Next test',exact=True).click();choose(p,'name','epic')
            check(p.locator('[data-action="save-exit"]').count()==0,'6: Save and finish has no overlapping Save and exit action')
            p.locator('[data-action="save-finish"]').click()
            check('2 tests saved · 1 still needs a choice' in p.locator('.walk-result').inner_text(),'6: walk completion reports skipped tests needing a decision')
        with case('once-6-8-walk-carry-and-wording') as p:
            p.locator('[data-inline="demo-tsh|name|epic"]').click();p.locator('[data-test="demo-tsh"]').first.click()
            check(p.locator('[role="dialog"]').count()==0 and p.evaluate('dirtyNow()') and not p.evaluate("byId('demo-tsh').decisions.name"),'7: opening the sole unsaved test carries the choice without saving or a dialog')
            check(p.locator('[data-answer="name:epic"]').get_attribute('aria-pressed')=='true','7: carried choice remains selected in the test editor')
            p.locator('[data-action="back-worklist"]').click();p.get_by_role('dialog').get_by_role('button',name='Discard',exact=True).click()
            for id in ['demo-tsh','demo-crp']:p.locator(f'[data-inline="{id}|name|epic"]').click()
            p.locator('[data-test="demo-tsh"]').first.click()
            check(p.get_by_role('dialog').is_visible(),'7: opening a test still warns when other tests have unsaved choices')
        with case('once-6-8-walk-carry-and-wording') as p:
            open_test(p,'sample-1')
            check(p.locator('[data-entry-field="labs"] [data-edit-field]').count()==0 and p.locator('.lab-managed').is_visible(),'8: editors see a plain lab-management note instead of a dead-end Edit')
            p.locator('#role').select_option('admin');check(p.locator('[data-entry-field="labs"] [data-nav="mapping"]').is_visible(),'8: administrators can open Lab mappings from the field')
            open_test(p,'demo-ferritin');check(p.locator('[data-set-aside="name"] [data-change-choice]').inner_text()=='Decide now' and p.locator('[data-action="resume-review"]').count()==0,'8: set-aside fields offer Decide now without a duplicate Review now action')
            p.locator('[data-nav="worklist"]').click();p.locator('[data-tab="all"]').click();p.locator('#all-filter').select_option('later')
            check(p.locator('.catalog-row').inner_text().count('Set aside')==1,'8: a Set aside row says Set aside only once')
    check(not errors,'No browser JavaScript exceptions')
    browser.close()
if ONLY is None:
    report={'verified_at':datetime.now(timezone.utc).isoformat(),'review':'Next fixes reviewed at 32260a9: consolidated saved changes, confirmation, cancel and source wording','commit':'pending-tested-source-commit','test_script':'https://amromeo.github.io/cuddly-garbanzo/check_workflows.py','passed':len(checks),'failed':0,'click_targets':metrics,'storage_key':'olsd-workflow-prototype-v7-test-by-test-20261103','sample_count':308,'patch_baseline':'96184ae','requested_checklist_status':'Browser checks cover all requested items 1–5 and the walk, carry and wording changes; previous workflow regressions retained.','review_baseline':'32260a9','source_sha256':hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':checks}
    (ROOT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'case':ONLY or 'all','passed':len(checks),'click_targets':metrics,'browser_errors':errors},indent=2))
