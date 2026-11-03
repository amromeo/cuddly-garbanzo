"""Browser regressions for the independent review. Run: python check_workflows.py [case-number]."""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib,json,os,sys,traceback
import openpyxl
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
BASE=os.environ.get('OLSD_TEST_URL','http://127.0.0.1:3000')
ONLY=int(sys.argv[1]) if len(sys.argv)>1 else None
checks=[];errors=[];active=0

def check(ok,name):
    if not ok: raise AssertionError(f'Item {active}: {name}')
    checks.append({'item':active,'description':name,'passed':True})

def open_test(p,id):
    p.goto(BASE+'/#/test?id='+id)
    p.locator('h1').wait_for()

def other(p,k):
    node=p.locator(f'[data-field="{k}"]')
    if node.count() and not node.is_visible():p.locator('.reference-fields > summary').click()

def edit(p,k,text):
    other(p,k)
    p.locator(f'[data-edit-field="{k}"]').click()
    p.locator(f'[data-edit="{k}"]').fill(text)

def choose(p,k,c):
    other(p,k);p.locator(f'[data-decision="{k}:{c}"]').click()

def save(p):p.locator('[data-action="save"]').click()
def approve(p):
    p.locator('[data-action="approve-one"]').click()
    p.get_by_role('button',name='Approve selected fields',exact=True).click()
def admin(p):
    p.locator('#role').select_option('admin')
def group(p,ids):
    p.goto(BASE+'/#/group?ids='+','.join(ids));p.locator('h1').wait_for()
def capture(p,name):p.screenshot(path=str(ROOT/'review-assets'/name),full_page=True)

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    @contextmanager
    def case(num,viewport=None):
        global active
        active=num
        ctx=browser.new_context(viewport=viewport or {'width':1450,'height':1100},accept_downloads=True)
        p=ctx.new_page();p.set_default_timeout(6000);p.on('pageerror',lambda error:errors.append(str(error)))
        p.goto(BASE);p.locator('h1').wait_for()
        try:yield p
        except Exception:
            traceback.print_exc()
            try:p.screenshot(path=str(ROOT/'review-assets'/f'failure-{num}.png'),full_page=True,timeout=2000)
            except Exception:pass
            raise
        finally:
            ctx.close()
            print('Completed case',num,flush=True)
    if ONLY in [None,1]:
        with case(1) as p:
            open_test(p,'demo-tsh')
            check(p.locator('[data-action="approve-one"]').is_disabled(),'Undecided TSH cannot be approved')
            check('Test name' in p.locator('#bar-message').inner_text(),'Approval blocker names the waiting field')
            p.evaluate("try { approveRecord(working); } catch(e) {}")
            check(p.evaluate('working.decisions.name===undefined && working.approval===null'),'Approval handler does not invent a decision')
            choose(p,'name','epic');save(p)
            p.locator('[data-action="approve-one"]').click()
            check('TSH, Third Generation' in p.locator('[role="dialog"]').inner_text(),'Approval comparison includes Epic’s actual value')
            p.get_by_role('button',name='Approve selected fields',exact=True).click()
            check(p.evaluate("byId('demo-tsh').decisions.name.choice==='epic' && byId('demo-tsh').proposed.name==='TSH, Third Generation'"),'Approved value matches the explicit Epic choice')
            check(p.evaluate("!!byId('demo-tsh').approval.basis.olsd && !!byId('demo-tsh').approval.basis.epic"),'Approval records exact source values and snapshot dates')
    if ONLY in [None,2]:
        with case(2) as p:
            group(p,['demo-tsh','785258','785260'])
            tsh=p.locator('[data-group-test="demo-tsh"]')
            check('TSH, Third Generation' in tsh.inner_text(),'Group review reveals open Epic name changes even when proposal equals OLSD')
            check(tsh.locator('[data-group]').count()==0,'Undecided test has no approval checkbox')
            check(p.locator('[data-group-test="785260"] [data-group]').count()==0,'Already-approved test has no reapproval checkbox')
            at=p.evaluate("byId('785260').approval.at")
            check(p.locator('[data-action="approve-group"]').is_disabled(),'Zero chosen approvals keeps group button disabled')
            open_test(p,'785258');choose(p,'labs','epic');save(p)
            group(p,['785258','785260'])
            box=p.locator('[data-group="785258"]')
            check(not box.is_checked(),'Eligible group approval starts unticked')
            box.check();check(p.locator('[data-action="approve-group"]').inner_text()=='Approve 1 update','Group button reports the selected approval count')
            p.locator('[data-action="approve-group"]').click()
            check(p.evaluate("byId('785260').approval.at")==at,'Group approval leaves existing approval time unchanged')
            capture(p,'group-review.png')
    if ONLY in [None,3]:
        with case(3) as p:
            open_test(p,'785258');p.locator('[data-include="labs"]').uncheck();save(p)
            check(p.evaluate("!!byId('785258').pending.labs"),'Unticking and saving does not resolve the source change')
            check(p.evaluate("matches(byId('785258'),'needs')"),'Excluded open source change remains in Needs review')
            check(p.locator('[data-action="approve-one"]').is_disabled(),'Excluding the unresolved field does not permit silent approval')
            open_test(p,'786513');p.locator('[data-include="labs"]').uncheck();save(p)
            check(p.locator('.blocker-card').is_visible(),'Unmapped laboratory remains prominently blocked when unticked')
            check(p.evaluate("byId('786513').blocked && matches(byId('786513'),'needs')"),'Mapping problem stays open independently of export inclusion')
            check(p.locator('[data-action="approve-one"]').is_disabled(),'Unmapping cannot be bypassed by a name-only selection')
            capture(p,'blocked-test.png')
    if ONLY in [None,4]:
        with case(4) as p:
            open_test(p,'demo-tsh');edit(p,'conditions','Discard this exact wording')
            before=p.evaluate('original.proposed.conditions')
            p.locator('#role').select_option('admin');p.get_by_role('button',name='Discard changes',exact=True).click()
            check(p.evaluate('working.proposed.conditions')==before,'Role-switch discard restores the saved working value')
            check(p.evaluate('!dirty && state.role==="admin"'),'Role switch completes after a real discard')
            choose(p,'name','epic');save(p);approve(p)
            check(p.evaluate("byId('demo-tsh').proposed.conditions")==before,'Approving later cannot save discarded text')
        with case(4) as p:
            open_test(p,'demo-tsh');edit(p,'conditions','Keep this unsaved text')
            p.locator('#role').select_option('admin');p.get_by_role('button',name='Stay',exact=True).click()
            check(p.locator('#role').input_value()=='editor' and p.locator('#top-role').input_value()=='editor','Stay restores both visible role selectors')
            check(p.evaluate('working.proposed.conditions')=='Keep this unsaved text','Stay preserves unsaved work')
            p.locator('[data-action="reset"]').first.click();p.get_by_role('button',name='Discard changes',exact=True).click()
            p.get_by_role('button',name='Cancel',exact=True).click()
            check(p.evaluate('working.proposed.conditions===original.proposed.conditions && !dirty'),'Discard also restores the working copy on the Reset route')
    if ONLY in [None,5]:
        with case(5) as p:
            open_test(p,'785260');edit(p,'conditions','Unsaved new rejection wording')
            check(p.locator('[data-action="download-one"]').is_disabled(),'Download is disabled while on-screen edits are unsaved')
            check('Saving will withdraw' in p.locator('#bar-message').inner_text(),'Approved-edit bar explains approval withdrawal')
            check('ready for' not in p.locator('#bar-message').inner_text(),'Dirty bar does not claim the changed content is approved')
            save(p)
            check(p.evaluate("byId('785260').approval.outdated"),'Saving an edited approval makes it out of date')
    if ONLY in [None,6]:
        with case(6) as p:
            open_test(p,'785260');ready_before=p.evaluate("state.tests.filter(ready).length")
            p.locator('[data-action="download-one"]').click()
            with p.expect_download() as info:p.get_by_role('button',name='Download Excel file',exact=True).click()
            dest=ROOT/'tested-export.xlsx';info.value.save_as(dest)
            check(openpyxl.load_workbook(dest).sheetnames==['Tests'],'Direct download is a readable Excel workbook')
            check(p.evaluate('state.tests.filter(ready).length')==ready_before-1,'Export reduces Ready to export count')
            check('Exported' in p.locator('.export-state').inner_text(),'Test displays exported date and filename')
            check(p.locator('[aria-current="step"]').get_attribute('data-stage')=='3','Progress reflects the exported stage')
            admin(p);p.locator('[data-nav="history"]').click();p.locator('[data-reconcile$=":match"]').click()
            open_test(p,'785260')
            check('Confirmed in snapshot' in p.locator('.export-state').inner_text(),'Matching snapshot produces an observed confirmation state')
            check(p.locator('[aria-current="step"]').get_attribute('data-stage')=='4','Progress reflects snapshot confirmation')
            check(p.evaluate("!ready(byId('785260'))"),'Confirmed update is not offered as new ready work')
            check('again' in p.locator('[data-action="download-one"]').inner_text(),'Downloading an exported version again is explicit')
    if ONLY in [None,7]:
        with case(7) as p:
            open_test(p,'demo-crp');choose(p,'name','epic');save(p);approve(p)
            p.goto(BASE+'/#/worklist?filter=ready')
            p.locator('[data-select="demo-crp"]').check();p.locator('[data-select="785260"]').check();p.locator('[data-action="download"]').click();p.get_by_role('button',name='Choose Excel files',exact=True).click()
            check(p.locator('[data-excel-download]').count()==2,'Different selected columns produce separately named files')
            check(p.evaluate('state.exports.length')==0,'Opening file chooser records no downloads')
            p.get_by_role('button',name='Done',exact=True).click()
            check(p.evaluate('state.exports.length')==0,'Done without downloading creates no export history')
            p.locator('[data-action="download"]').click();p.get_by_role('button',name='Choose Excel files',exact=True).click()
            with p.expect_download() as info:p.locator('[data-excel-download="0"]').click()
            info.value.save_as(ROOT/'tested-one-of-two.xlsx')
            check(p.evaluate('state.exports.length')==1,'Only the clicked file is recorded')
            check(p.locator('[data-file-status="0"]').inner_text().startswith('Downloaded'),'Chooser shows downloaded status per file')
            check(p.locator('[data-file-status="1"]').inner_text()=='Not downloaded','Other file remains explicitly not downloaded')
            check(p.evaluate("state.exports[0].tests.length")==1,'Only the downloaded file’s test is marked exported')
    if ONLY in [None,8]:
        with case(8) as p:
            open_test(p,'785258');choose(p,'labs','epic');edit(p,'conditions','My saved rejection text');save(p);approve(p);admin(p)
            p.locator('[data-nav="worklist"]').click();p.locator('[data-action="snapshot"]').click();p.get_by_role('button',name='Load newer example snapshot',exact=True).click()
            check(p.evaluate("byId('785258').approval.outdated"),'Unexpected OLSD change invalidates an included-field approval')
            check(p.evaluate("matches(byId('785258'),'needs')"),'Changed OLSD source returns approved work to Needs review')
            open_test(p,'785258')
            check(p.evaluate('working.proposed.conditions')=='My saved rejection text','New snapshot preserves the saved authored text')
            check(p.locator('[data-region="needs"] [data-field="conditions"]').is_visible(),'Changed included OLSD value appears outside Other fields')
            check(p.evaluate("byId('785258').approval.basis.olsd.conditions")!='Illustrative newer OLSD wording from the uploaded export.','Approval retains the original exact OLSD basis')
        with case(8) as p:
            admin(p);p.locator('[data-action="snapshot"]').click();p.get_by_role('button',name='Load newer example snapshot',exact=True).click();open_test(p,'785258')
            check(p.locator('[data-region="needs"] [data-field="conditions"]').is_visible(),'Unselected changed OLSD field is still visible as open work')
            check('OLSD changed since the last snapshot' in p.locator('[data-field="conditions"]').inner_text(),'Unselected source notice explains what changed')
            check(not p.locator('[data-include="conditions"]').is_checked(),'Snapshot does not silently select an optional field for export')
            p.evaluate("applySource('Epic',{'785260':{name:'New Epic CBC name'}});render();")
            check(p.evaluate("byId('785260').approval.outdated && !!byId('785260').pending.name"),'New Epic values also invalidate included approved source basis')
    if ONLY in [None,9]:
        with case(9) as p:
            open_test(p,'demo-crp');choose(p,'name','olsd')
            check(p.evaluate('working.proposed.name===working.olsd.name'),'Keep current OLSD value means the observed OLSD value, not the saved draft')
            save(p);check(p.evaluate("!byId('demo-crp').draft && !canApprove(byId('demo-crp'))"),'Pure keep finishes on save without approval or export')
            open_test(p,'demo-tsh');choose(p,'name','epic');edit(p,'name','My deliberate custom catalog name');save(p)
            check(p.evaluate("byId('demo-tsh').decisions.name.choice")== 'custom','Typing after Use Epic switches to Use my wording')
            check(p.evaluate("matches(byId('demo-tsh'),'reviewed')"),'Custom wording different from Epic appears in Reviewed differences')
            check(p.locator('[data-decision="name:custom"]').get_attribute('aria-pressed')=='true','Displayed choice follows the actual custom value')
    if ONLY in [None,10]:
        with case(10) as p:
            open_test(p,'785258')
            check(p.locator('[data-proposed-value="labs"]').inner_text().splitlines()==['Hematology Laboratory Main Hospital','Hematology Laboratory KOP'],'Proposed performing laboratories preserve their separate lines')
            check(p.locator('[data-proposed-value="labs"]').evaluate("n=>getComputedStyle(n).whiteSpace")=='pre-wrap','Browser styling preserves laboratory line breaks')
    if ONLY in [None,11]:
        with case(11) as p:
            open_test(p,'demo-tsh');choose(p,'name','epic');save(p)
            check(p.locator('[data-region="decided"] [data-field="name"]').is_visible(),'Saved Epic choice appears under Decided rather than Needs a decision')
            check(p.locator('[data-region="needs"]').count()==0,'Decided header does not contradict completed decisions')
            choose(p,'name','olsd');save(p)
            check(p.locator('[data-region="decided"] [data-field="name"]').is_visible(),'Keep decision remains visible and changeable')
            check(p.locator('[data-decision="name:epic"]').is_visible(),'A kept decision can be changed without opening hidden reference fields')
            open_test(p,'785260')
            check(p.locator('[data-region="approved"] [data-field="conditions"]').is_visible(),'Approved conditions appear under Approved changes')
            check(p.locator('.reference-fields [data-field="conditions"]').count()==0,'Approved change is not labeled completeness-only')
            admin(p);p.locator('[data-nav="mapping"]').click();p.locator('#map-name').fill('Chemistry Laboratory KOP Hospital');p.locator('[data-action="mapping-preview"]').click();p.get_by_role('button',name='Save mapping & selected approvals',exact=True).click()
            check('No test updates were approved' in p.locator('#toast').inner_text(),'Saving an unselected mapping does not claim approvals occurred')
    if ONLY in [None,13]:
        with case(13) as p:
            p.locator('[data-select="785258"]').check();p.locator('#search').fill('Ferritin')
            check(p.locator('[data-test="demo-ferritin"]').is_visible(),'Search finds deferred tests outside the active tab')
            check(p.evaluate('selected.size')==0,'Changing search clears previously hidden selected rows')
            p.locator('#search').fill('CBC with Differential')
            check(p.locator('[data-test="785260"]').is_visible(),'Search also finds already approved tests outside Needs review')
    if ONLY in [None,14]:
        with case(14) as p:
            open_test(p,'demo-tsh');other(p,'conditions')
            check(p.locator('[data-edit-field="conditions"]').is_visible(),'Other fields expose an explicit Edit action')
            p.locator('[data-edit-field="conditions"]').click()
            check(p.locator('[data-include="conditions"]').is_checked(),'Edit automatically includes the field in the update')
            check(p.locator('#edit-conditions').is_editable(),'Edit directly enables authoring instead of requiring a checkbox guess')
    if ONLY in [None,15]:
        with case(15) as p:
            check(p.evaluate('state.tests.length')>=300,'Sample catalog includes hundreds of records')
            check('name changes' in p.locator('.nightly-summary').inner_text(),'Nightly summary reports types of source changes')
            check(p.locator('.stats').count()==0,'Worklist uses one set of status filters rather than duplicate tiles')
            check(p.locator('[data-action="group"]').get_attribute('class')=='primary','Review selected is the primary Needs review action')
            check(p.locator('[data-workflow-status="pending"]').first.inner_text()=='No draft','Untouched tests say No draft')
            p.locator('[data-filter="all"]').click();p.get_by_role('button',name='Next',exact=True).click()
            check('page 2' in p.locator('.pagination').inner_text(),'Catalog pagination advances to another page')
            p.locator('#sort').select_option('asc');titles=p.locator('.test-link').all_text_contents()
            check(titles[0]=='Basic Metabolic Panel','Sorting orders the catalog by name')
            p.locator('#change-type').select_option('mapping')
            check(p.locator('[data-test="786513"]').is_visible() and p.locator('.test-link').count()==1,'Mapping change-type filter narrows review naturally')
            p.locator('#lab-filter').select_option('UC HEMATOLOGY')
            check(p.locator('.test-link').count()==0,'Lab filter combines with the selected change type')
    if ONLY in [None,16]:
        with case(16) as p:
            open_test(p,'demo-tsh');choose(p,'name','epic');save(p)
            check(p.locator('[data-field="name"] ins').count()>0 and p.locator('[data-field="name"] del').count()>0,'Comparison highlights added and removed words')
            p.locator('[data-action="approve-one"]').click()
            check(p.locator('[role="dialog"] ins').count()>0 and p.locator('[role="dialog"] del').count()>0,'Approval dialog includes highlighted differences')
            p.get_by_role('button',name='Back to editing',exact=True).click()
            edit(p,'name','Custom TSH public name');p.locator('[data-action="unsaved-details"]').click()
            check(p.locator('[role="dialog"] ins').count()>0 and p.locator('[role="dialog"] del').count()>0,'Unsaved comparison highlights exact text changes')
            p.get_by_role('button',name='Continue editing',exact=True).click();save(p);group(p,['demo-tsh'])
            check(p.locator('.group-test ins').count()>0 and p.locator('.group-test del').count()>0,'Group review also highlights differences')
    if ONLY in [None,17]:
        with case(17) as p:
            open_test(p,'demo-tsh');choose(p,'name','olsd');p.locator('#note-name').fill('Public wording intentionally preserved');save(p)
            p.locator('.test-history > summary').click()
            check('Public wording intentionally preserved' in p.locator('.test-history').inner_text(),'Saved decision reason appears in test history')
            p.locator('.nav[data-nav="system"]').click();p.locator('[data-action="next-epic"]').click();open_test(p,'demo-tsh')
            text=p.locator('.prior-decision').inner_text()
            check('Public wording intentionally preserved' in text and 'Epic then' in text and 'Epic now' in text,'Returned review shows prior kept choice, reason, and old/new Epic values')
            open_test(p,'demo-ferritin')
            check('Waiting for laboratory guidance' in p.locator('#content').inner_text(),'Deferred record displays its saved reason')
    if ONLY in [None,18]:
        with case(18) as p:
            open_test(p,'demo-tsh');choose(p,'name','olsd');save(p)
            check(p.evaluate("!matches(byId('demo-tsh'),'drafts') && matches(byId('demo-tsh'),'reviewed')"),'Unchanged keep leaves Drafts and remains in Reviewed differences')
            check(p.locator('[data-action="approve-one"]').count()==0,'Pure keep offers no approval for an unchanged file')
            check(p.locator('[data-action="download-one"]').count()==0,'Pure keep offers no unnecessary export')
    if ONLY in [None,19]:
        with case(19) as p:
            open_test(p,'786513')
            check('save your draft' not in p.locator('.blocker-card').inner_text().lower(),'Blocker does not tell an untouched user to use disabled Save')
            p.locator('[data-request="786513"]').click();p.get_by_role('button',name='Note request in prototype',exact=True).click()
            check('No message was sent' in p.locator('#toast').inner_text(),'Administrator request is a clearly identified local placeholder')
            p.locator('[data-blocker="786513"]').first.click();admin(p)
            p.locator('#map-name').fill('Chemistry Laboratory KOP Hospital');p.locator('[data-action="mapping-preview"]').click();p.get_by_role('button',name='Save mapping & selected approvals',exact=True).click()
            check(p.locator('tr').filter(has_text='KH CHEMISTRY').filter(has_text='Chemistry Laboratory KOP Hospital').count()==1,'New mapping appears in Existing mappings')
            p.locator('[data-action="mapping-back"]').click()
            check(p.locator('h1').inner_text()=='Basic Metabolic Panel','Mapping flow provides a direct return to the test')
    if ONLY in [None,20]:
        with case(20) as p:
            open_test(p,'demo-tsh');choose(p,'name','epic');save(p)
            toast=p.locator('.toast').bounding_box();bar=p.locator('.sticky-actions').bounding_box()
            check(toast['y']+toast['height']<bar['y'],'Save notification does not cover approval or save controls')
    if ONLY in [None,21]:
        with case(21) as p:
            body=p.locator('body').inner_text()
            check(all(x not in body for x in ['Your catalog, kept in step','Review what changed. Keep what is intentional.','Designed around your catalog work.']),'Promotional worklist slogans were removed')
            p.locator('.nav[data-nav="system"]').click()
            check('Freshness & operating context' not in p.locator('body').inner_text(),'System wording stays task-specific')
    if ONLY in [None,22]:
        with case(22) as p:
            check('OLSD snapshot updates · administrators only' not in p.locator('body').inner_text(),'Editor worklist omits irrelevant administrator-only upload text')
            open_test(p,'demo-tsh');other(p,'conditions')
            check('Sample record' in p.locator('.identity').inner_text(),'Sample identity wording avoids fixture terminology')
            check('Comes from' in p.locator('[data-field="conditions"]').text_content(),'Field provenance uses plain Comes from wording')
    if ONLY in [None,23]:
        with case(23) as p:
            check(p.locator('#actor-label').inner_text()=='Demo editor','Top identity consistently starts with Demo editor')
            admin(p);check(p.locator('#actor-label').inner_text()=='Demo administrator','Top identity follows administrator role changes')
            p.locator('#role').select_option('editor');check(p.locator('#actor-label').inner_text()=='Demo editor','Role can be switched back consistently')
            check('Demo steward' not in p.locator('body').inner_text(),'Role labels do not mix editor and steward')
    if ONLY in [None,24]:
        with case(24) as p:
            text=p.locator('.statusline').inner_text()
            check('2026' in text and ('EST' in text or 'EDT' in text) and 'old)' in text,'Source dates include year, time zone, and age')
            p.evaluate("state.epicDate='2020-01-01T00:00:00Z';render();")
            check(p.locator('.dot.overdue').count()==1 and 'overdue' in p.locator('.statusline').inner_text(),'Overdue source check changes its indicator and text')
    if ONLY in [None,25]:
        with case(25) as p:
            p.locator('[data-select="785258"]').check()
            check(p.locator('[data-select="785258"]').evaluate('n=>n===document.activeElement'),'Row checkbox retains keyboard focus')
            p.locator('[data-filter="drafts"]').click()
            check(p.locator('[data-filter="drafts"]').evaluate('n=>n===document.activeElement'),'Changing worklist view restores focus to its button')
            open_test(p,'demo-tsh');choose(p,'name','olsd')
            check(p.locator('[data-decision="name:olsd"]').evaluate('n=>n===document.activeElement'),'Decision remains focused after moving into Decided')
            p.locator('[data-action="unsaved-details"]').click();p.get_by_role('button',name='Continue editing',exact=True).click()
            check(p.locator('[data-action="unsaved-details"]').evaluate('n=>n===document.activeElement'),'Dialog returns focus to its actual opener')
    if ONLY in [None,26]:
        with case(26) as p:
            open_test(p,'demo-tsh')
            check(p.locator('.comparison-table thead th[scope="col"]').count()>=3,'Comparison exposes real table column headers')
            check(p.locator('[data-field="name"] td[aria-label]').count()==3,'Each compared value is associated with its field and column')
            check(p.locator('[role="status"]').count()==1,'Only one live status region exists, rather than every chip')
    if ONLY in [None,27]:
        with case(27) as p:
            check(p.locator('[role="tab"]').count()==0 and p.locator('.tabs button[aria-pressed]').count()>0,'Worklist filters use plain accessible buttons instead of incomplete tabs')
    if ONLY in [None,28]:
        with case(28) as p:
            open_test(p,'demo-tsh');other(p,'conditions')
            check(p.locator('.note-label').first.evaluate('n=>parseFloat(getComputedStyle(n).fontSize)')>=12,'Essential note labels meet the 12px minimum')
            # WCAG luminance contrast for the requested muted foreground/background pair.
            def luminance(hexcode):
                xs=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
                xs=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in xs]
                return sum(a*b for a,b in zip(xs,[.2126,.7152,.0722]))
            ratio=(luminance('f5f7f4')+.05)/(luminance('5c7070')+.05)
            check(ratio>=4.5,'Muted text meets normal-text contrast on the page background')
    if ONLY in [None,29]:
        with case(29) as p:
            open_test(p,'786513');other(p,'categories');p.locator('[data-edit-field="categories"]').click()
            p.locator('[data-detail="786513:categories"] > summary').click()
            box=p.locator('[data-category="* Emergency Test List"]');box.click();check(p.get_by_role('dialog').is_visible(),'Removing an existing category opens a confirmation');p.keyboard.press('Escape')
            check(p.locator('[data-category="* Emergency Test List"]').is_checked(),'Escape restores the category checkbox to the unchanged draft')
            p.locator('[data-category="Hematology Laboratory"]').check()
            check(p.locator('[data-detail="786513:categories"]').get_attribute('open') is not None,'Additional-category section stays open after ticking')
            save(p)
            path=p.url;p.reload()
            check(p.url==path and p.locator('h1').inner_text()=='Basic Metabolic Panel','Refresh restores the selected test URL')
            p.locator('.nav[data-nav="system"]').click();p.go_back()
            check(p.locator('h1').inner_text()=='Basic Metabolic Panel','Browser Back navigates within the app')
        with case(29,{'width':390,'height':844}) as p:
            p.locator('.top-controls > summary').click();p.locator('#top-role').select_option('admin')
            check(p.locator('#actor-label').inner_text()=='Demo administrator','Phone role selector can enter administrator mode')
            p.locator('#top-role').select_option('editor')
            check(p.locator('#actor-label').inner_text()=='Demo editor','Phone role selector can return to editor without resetting')
            check(p.locator('.top-controls [data-action="reset"]').is_visible(),'Reset is available in phone demo controls')
            check(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Worklist fits the phone viewport')
            capture(p,'mobile-worklist.png')
    check(not errors,'No browser JavaScript exceptions')
    browser.close()
if ONLY is None:
    report={'verified_at':datetime.now(timezone.utc).isoformat(),'commit':os.environ.get('OLSD_TEST_COMMIT','pending-source-commit'),'test_script':'https://amromeo.github.io/cuddly-garbanzo/check_workflows.py','source_sha256':hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'passed':len(checks),'failed':0,'section_1_items_covered':sorted(set(c['item'] for c in checks if c['item']<=11)),'checks':checks}
    (ROOT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'case':ONLY or 'all','passed':len(checks),'browser_errors':errors},indent=2))
