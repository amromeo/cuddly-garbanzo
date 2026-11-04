library(shiny)
for(f in c('core','storage','sources','exports')) source(file.path('R',paste0(f,'.R')),local=TRUE)
cfg<-config();board<-board_for(cfg);process_lock<-acquire_process_lock(cfg)
store<-new_store(pin_backend(board,cfg$pin,cfg$initialize||!cfg$hosted),cfg)
button <- function(label,command,id='',field='',class='') tags$button(type='button',class=paste('btn btn-default',class),`data-command`=command,`data-id`=id,`data-field`=field,label)
difference <- function(value,other) {
 a<-strsplit(value,'',fixed=TRUE)[[1]];b<-strsplit(other,'',fixed=TRUE)[[1]];prefix<-0L;suffix<-0L
 while(prefix<min(length(a),length(b))&&a[[prefix+1L]]==b[[prefix+1L]]) prefix<-prefix+1L
 while(suffix<min(length(a),length(b))-prefix&&a[[length(a)-suffix]]==b[[length(b)-suffix]]) suffix<-suffix+1L
 part<-function(from,to) if(from>to) '' else paste(a[from:to],collapse='')
 htmltools::HTML(paste0(htmltools::htmlEscape(part(1L,prefix)),'<mark>',htmltools::htmlEscape(part(prefix+1L,length(a)-suffix)),'</mark>',htmltools::htmlEscape(part(length(a)-suffix+1L,length(a)))))
}
value_block <- function(label,value,compare=NULL) tags$div(class='value-block',tags$strong(label),tags$pre(
 if(is.null(value)) tags$em('No corresponding Epic value') else if(!is.null(compare)&&!identical(value,compare)) difference(value,compare) else value),
 if(!is.null(compare)&&identical(value,compare)) tags$small('Unchanged'))
ui<-fluidPage(tags$head(tags$link(rel='stylesheet',href='pilot.css'),tags$script(src='pilot.js')),
 tags$header(tags$a(href='#worklist',class='brand','OLSD Catalog manager'),uiOutput('navigation')),
 uiOutput('connection'),uiOutput('filters'),uiOutput('page'),tags$div(id='live',role='status',`aria-live`='polite'),uiOutput('savebar'))
server<-function(input,output,session) {
 actor<-actor_for(session,cfg);token<-session$token
 s<-reactiveVal(store$read());view<-reactiveVal('worklist');test_id<-reactiveVal(NULL);tab<-reactiveVal('To review');origin<-reactiveVal('To review')
 carried<-reactiveVal(NULL);queue<-reactiveVal(character());walking<-reactiveVal(FALSE);walk_saved<-reactiveVal(character());edits<-reactiveVal(character());drafts<-reactiveVal(list());upload<-reactiveVal(NULL);export_plan<-reactiveVal(list());action_pending<-reactiveVal(NULL);message<-reactiveVal('');source_error<-reactiveVal('')
 revision<-reactiveVal(isolate(s())$revision)
 notify<-function(x) message(x)
 attempt<-function(fn) tryCatch(fn(),error=function(e) {showNotification(conditionMessage(e),type='error',duration=NULL);FALSE})
 write<-function(action,admin=FALSE) {
  require_role(actor,admin)
  result<-store$commit(actor,token,revision(),paste0(token,'-',now(),'-',runif(1)),action)
  s(result);revision(result$revision);TRUE
 }
 session$onSessionEnded(function() store$release(token))
 output$navigation<-renderUI(tagList(button('Worklist','worklist'),button('Downloads','downloads'),if(actor$role=='admin') tagList(button('Update OLSD snapshot','snapshot'),button('Lab mappings','mappings'))))
 output$connection<-renderUI(tags$div(class='connection',
  if(!cfg$hosted) tags$strong('Local development · '),paste(actor$user,if(actor$role=='admin') 'administrator' else actor$role,sep=' · '),
  button('Reload saved state','reload'),
  tags$p(paste('Epic:',display_date(s()$sources$epic$at),'· OLSD:',display_date(s()$sources$olsd$at))),
  if(nzchar(source_error())) tags$p(class='warning',source_error()),
  if(actor$user!=cfg$writer) tags$p('Viewing only. The designated pilot operator makes changes.'),
  if(nzchar(message())) tags$p(role='status',message())))
 observeEvent(TRUE,{
  if(nzchar(cfg$source_pin)&&pins::pin_exists(board,cfg$source_pin)) {
   attempt(function(){src<-read_epic_pin(board,cfg$source_pin);source_error(if(!identical(src$reference$hash,s()$sources$epic$hash)) 'A newer Epic source is available. The pilot operator can apply it.' else '')})
  }
 },once=TRUE)
 observe({invalidateLater(60000,session);tryCatch({
  if(pins::pin_exists(board,cfg$source_pin)) {src<-read_epic_pin(board,cfg$source_pin)
   if(!identical(src$reference$hash,s()$sources$epic$hash)) {
    if(identical(actor$user,cfg$writer)&&!isTRUE(input$pilot_dirty)&&!length(drafts())&&length(s()$tests)) {
     tryCatch({write(function(st) apply_epic(st,src$rows,src$reference,actor));source_error('')},error=function(e) source_error(paste('A newer Epic source is available.',conditionMessage(e))))
    } else source_error('A newer Epic source is available. Save your work, then apply it.')
   }
   else if(difftime(Sys.time(),as.POSIXct(src$fetched_at,format='%Y-%m-%dT%H:%M:%OSZ',tz='UTC'),units='hours')>30) source_error('The Epic source check is overdue.') else source_error('');status_pin<-paste0(cfg$source_pin,'-status');if(pins::pin_exists(board,status_pin)&&identical(pins::pin_read(board,status_pin)$ok,FALSE)) source_error('The nightly Epic refresh failed. Last successful source retained; contact the administrator.')}
 },error=function(e) source_error(paste('Epic source unavailable; retaining the last successful version.',conditionMessage(e))))})
 observe({
  invalidateLater(5000,session)
  tryCatch({latest<-store$read();if(latest$revision!=revision()) {
   if(!length(drafts())&&!isTRUE(input$pilot_dirty)) {s(latest);revision(latest$revision)}
   else source_error('Newer saved work is available. Reload saved state to compare it with your unsaved choices.')
  }},error=function(e) source_error(paste('Saved state unavailable. Your current work is retained.',conditionMessage(e))))
 })
 selected<-reactive(input$selected%||%character())
 rows<-reactive({
  ts<-s()$tests;q<-tolower(input$search%||%'');filter<-input$lab%||%'All'
  if(nzchar(q)) ts<-Filter(function(t) grepl(q,tolower(paste(t$olsd$name,t$number,t$id)),fixed=TRUE),ts)
  else ts<-Filter(function(t) {st<-status(s(),t);switch(tab(),'To review'=st%in%c('To review','Waiting on mapping'),'To approve'=st=='To approve','To download'=st=='To download','Kept wording'=st=='Kept wording','Set aside'=st=='Set aside','Source issues'=st=='Source issues',TRUE)},ts)
  if(filter!='All') ts<-Filter(function(t) identical(t$section,filter),ts)
  if(tab()=='To review'&&!nzchar(q)) ts<-ts[order(vapply(ts,function(t) {n<-length(open_fields(t));if(length(t$blocked)) 5 else if(n>1) 1 else if('name'%in%open_fields(t)) 2 else if('labs'%in%open_fields(t)) 3 else 4},numeric(1)))]
  ts
 })
 observeEvent(list(input$search,input$lab),{session$sendCustomMessage('selectRows',character())},ignoreInit=TRUE)
 current<-reactive(s()$tests[[test_id()]])
 capture<-function() {
  if(view()!='test'||is.null(current())) return()
  id<-test_id();ds<-drafts();d<-ds[[id]]%||%list();t<-current()
  for(k in unique(c(open_fields(t),edits()))) {
   c<-input[[paste0('choice_',k)]]%||%'';if(!nzchar(c)) next
   v<-input[[paste0('value_',k)]]%||%t$proposed[[k]];if(k=='categories') v<-paste(v,collapse=';')
   n<-input[[paste0('note_',k)]]%||%'';old<-t$choices[[k]]
   d[[k]]<-list(choice=c,value=v,note=n)
  }
  if(length(d)) ds[[id]]<-d;drafts(ds)
 }
 navigate<-function(target,id=NULL,guard=TRUE) {
  capture()
  action<-function(){if(target!='test') walking(FALSE);view(target);test_id(id);edits(character());session$sendCustomMessage('route',if(target=='test') paste0('test/',id) else target)}
  if(guard&&length(drafts())) {action_pending(action);showModal(modalDialog(title='Unsaved choices',tags$p('Your unsaved choices remain until you save or discard them.'),uiOutput('unsaved'),footer=tagList(button('Stay','stay'),button('Discard changes','discard'),button('Save and continue','save_continue'))))} else action()
 }
 output$unsaved<-renderUI(tagList(lapply(names(drafts()),function(id) tagList(tags$h3(s()$tests[[id]]$olsd$name),lapply(names(drafts()[[id]]),function(k){d<-drafts()[[id]][[k]];tagList(tags$h4(fields[[k]]),value_block('Saved proposal',s()$tests[[id]]$proposed[[k]]),value_block('Unsaved choice',switch(d$choice,custom=d$value,epic=s()$tests[[id]]$epic[[k]],olsd=s()$tests[[id]]$olsd[[k]],later='Decide later')))})))))
 save_all<-function() {capture();ds<-drafts();if(!length(ds)) fail('No unsaved choices.')
  write(function(st) {for(id in names(ds)) st<-apply_choices(st,id,ds[[id]],actor);st})
  walk_saved(unique(c(walk_saved(),names(ds))));drafts(list());edits(character());session$sendCustomMessage('saved',TRUE);notify('Choices saved. Saving does not approve changes.');TRUE
 }
 step<-function(direction,finish=FALSE) {
  q<-queue();i<-match(test_id(),q)
  if(finish||is.na(i)||i+direction>length(q)) {remaining<-sum(vapply(s()$tests[q],function(t) length(open_fields(t))>0,logical(1)));notify(paste(length(walk_saved()),'tests saved ·',remaining,'still need a choice'));navigate('worklist',guard=TRUE)}
  else if(i+direction>0) navigate('test',q[[i+direction]],guard=TRUE)
 }
 output$filters<-renderUI(if(view()=='worklist') tags$div(class='filters',textInput('search','Search all tests',value=isolate(input$search)%||%''),selectInput('lab','Lab section',c('All',sort(unique(vapply(s()$tests,function(t)t$section,character(1))))),selected=isolate(input$lab)%||%'All')))
 section_for<-function(t) {
  if(isTRUE(t$source_conflict)) return('Procedure assignments')
  if(length(t$blocked)) return('Waiting on lab names')
  keys<-open_fields(t)
  if(length(keys)>1) 'More than one change' else if('name'%in%keys) 'Name changes' else if('labs'%in%keys) 'Lab changes' else 'Other changes'
 }
 worklist<-function() {
  ts<-rows();statuses<-vapply(s()$tests,function(t) status(s(),t),character(1));counts<-table(statuses)
  counts['To review']<-sum(statuses%in%c('To review','Waiting on mapping'))
  row<-function(t) tags$tr(
   tags$td(tags$input(type='checkbox',class='row-select',value=t$id,checked=if(t$id%in%isolate(selected())) 'checked' else NULL,`aria-label`=paste('Select',t$olsd$name))),
   tags$td(button(t$olsd$name,'open',t$id),tags$p(paste(t$number,'·',t$id,'·',t$section))),
   tags$td(lapply(open_fields(t),function(k) {
    staged<-drafts()[[t$id]][[k]]
    tags$div(tags$strong(fields[[k]]),value_block('OLSD',t$olsd[[k]],t$epic[[k]]),value_block('Epic',t$epic[[k]],t$olsd[[k]]),
     if(!is.null(t$pending[[k]]$saved)&&!same(t$pending[[k]]$saved,t$epic[[k]],k)&&!same(t$pending[[k]]$saved,t$olsd[[k]],k)) value_block('Saved wording',t$pending[[k]]$saved),
     if(!is.null(staged)) tags$strong('Unsaved'),
     if(k%in%c('name','labs')&&!k%in%t$blocked) tagList(button('Use Epic','inline_epic',t$id,k,class=if(identical(staged$choice,'epic')) 'active' else ''),button('Keep','inline_olsd',t$id,k,class=if(identical(staged$choice,'olsd')) 'active' else '')) else tags$p('Open this test to review the change.'),
     if(identical(t$choices[[k]]$choice,'later')) tags$p(paste('Set aside:',t$choices[[k]]$note)))
   }),lapply(setdiff(names(t$choices),open_fields(t)),function(k) tags$p(paste(fields[[k]],t$choices[[k]]$choice,t$proposed[[k]],t$choices[[k]]$note)))),
   tags$td(status(s(),t)))
  table_rows<-if(tab()=='To review'&&!nzchar(input$search%||%'')) lapply(c('More than one change','Name changes','Lab changes','Other changes','Procedure assignments','Waiting on lab names'),function(group) {
   members<-Filter(function(t) section_for(t)==group,ts)
   if(length(members)) tagList(tags$tr(tags$th(colspan=4,paste(group,'·',length(members)),button('Select section','select_group',group))),lapply(members,row))
  }) else lapply(ts,row)
  tagList(tags$h1('Catalog worklist'),tags$div(class='tabs',lapply(c('To review','To approve','To download','Kept wording','Set aside','Source issues','All tests'),function(x) button(paste(x,if(x=='All tests') length(s()$tests) else if(x%in%names(counts)) unname(counts[x]) else 0),'tab',x,class=if(tab()==x) 'active' else ''))),
   tags$p(paste(length(ts),'of',if(nzchar(input$search%||%'')) length(s()$tests) else if(tab()=='All tests') length(s()$tests) else if(tab()%in%names(counts)) counts[tab()] else 0,'tests')),
   tags$p(paste('Open changes:',sum(vapply(s()$tests,function(t) 'name'%in%open_fields(t),logical(1))),'names ·',sum(vapply(s()$tests,function(t) 'labs'%in%open_fields(t),logical(1))),'labs ·',sum(vapply(s()$tests,function(t) length(t$blocked)>0,logical(1))),'mapping problems')),
   button('Apply latest Epic source','apply_source'),
   tags$div(class='selection',button('Select all shown','select_all'),button('Clear selection','clear_selection'),button('Review one by one','walk'),
    if(tab()=='To review') tagList(button('Use Epic for selected name/lab changes','bulk_epic'),button('Keep what is in the OLSD','bulk_olsd'),button('Decide later','bulk_later')),
    if(tab()=='To approve') tagList(button('Approve selected tests','approve_selected'),button('Send selected back to review','send_selected')),
    if(tab()=='To download') tagList(button('Prepare selected Excel files','prepare'),button('Withdraw selected approvals','send_selected'))),
   tags$table(class='worklist',tags$thead(tags$tr(tags$th('Select'),tags$th('Catalog test'),tags$th('Changes and saved choices'),tags$th('Status'))),tags$tbody(table_rows)))
 }
 field_cards<-function(t,k) {
  d<-isolate(drafts()[[t$id]][[k]]);options<-c('Keep what is in the OLSD'='olsd')
  if(!is.null(t$epic[[k]])&&!same(t$epic[[k]],t$olsd[[k]],k)&&!k%in%t$blocked) options<-c('Use Epic’s version'='epic',options,'Decide later'='later')
  if(k!='labs') options<-c(options,'Use my wording'='custom')
  saved<-t$choices[[k]]$previous$value%||%t$pending[[k]]$saved%||%t$proposed[[k]]
  tags$section(class='field-card',tags$h3(paste(fields[[k]],': what should the catalog say?')),
   tags$div(class='comparison',value_block('In OLSD now',t$olsd[[k]],t$proposed[[k]]),value_block('Epic',t$epic[[k]],t$olsd[[k]]),value_block('Saved wording',saved)),
   radioButtons(paste0('choice_',k),'Choose an outcome',choices=options,selected=d$choice%||%character()),
   if(k!='labs') if(k=='categories') selectizeInput(paste0('value_',k),'Approved categories',s()$categories,multiple=TRUE,selected=strsplit(d$value%||%saved,';',fixed=TRUE)[[1]]) else textAreaInput(paste0('value_',k),'My wording',value=d$value%||%saved,width='100%'),
   if(nzchar(t$choices[[k]]$note%||%'')) tags$p(paste('Earlier note:',t$choices[[k]]$note)),textInput(paste0('note_',k),'Optional note',value=d$note%||%''),if(k=='categories') tags$p('OLSD imports append categories. Removing a selection here cannot remove an existing OLSD category; an administrator must remove it in OLSD.'),
   if(k%in%edits()) button('Cancel','cancel_edit',field=k))
 }
 output$linked_procedures<-renderTable({req(current());d<-current()$linked_procedures;if(is.null(d)) return(NULL);out<-d[,intersect(c('epic_id','name','sections','link_label'),names(d)),drop=FALSE];names(out)<-c('Procedure ID','Epic display name','Lab sections','Link label')[seq_len(ncol(out))];out})
 testpage<-function() {
  t<-current();if(is.null(t)) return(tags$p('Test not found.'))
  open<-unique(c(open_fields(t),edits()));saved<-setdiff(names(t$choices),open);other<-setdiff(names(fields),c(open,saved))
  tagList(button(paste('Back to',origin()),'back'),tags$h1(t$olsd$name),tags$p(paste(t$number,'· OLSD',t$id,'· Epic',t$epic_id)),if(nzchar(t$link_label%||%'')) tags$p(paste('Epic link:',t$link_label)),if(isTRUE(t$shared_procedure)) tags$p('This Epic procedure links to multiple OLSD entries. Review each entry separately; keep specimen-specific OLSD names unless you explicitly choose a replacement.'),tags$p(status(s(),t)),tags$p(paste('OLSD observed:',display_date(t$sources$olsd$at),'· Epic checked:',display_date(t$sources$epic$at))),
   tags$div(class='steps',paste('Compare & edit →',if(ready(t)) 'Approved → Download / confirm' else 'Review & approve → Download / confirm')),
   if(!is.null(t$linked_procedures)) tags$section(tags$h2('Linked Epic procedures'),tableOutput('linked_procedures'),
    if(isTRUE(t$source_issue)) tags$div(class='blocker',tags$strong('Set aside: missing Epic display name.'),tags$p('This entry is retained for later source correction. Current OLSD content is unchanged; it cannot be approved or exported using incomplete source data. Other entries can continue.')),
    if(isTRUE(t$source_conflict)&&!isTRUE(t$source_issue)) tags$div(class='blocker',tags$strong('Choose which Epic procedure drives this OLSD entry.'),tags$p('The linked procedures have conflicting source values, or the previous assignment is no longer linked. Current OLSD content is preserved; approval is unavailable until an administrator resolves the assignment.')),
    if(actor$role=='admin') tagList(selectInput('primary_procedure','Procedure that drives updates',choices=c('Select a procedure'='',setNames(t$linked_procedures$epic_id,paste(t$linked_procedures$epic_id,t$linked_procedures$name,sep=' · '))),selected=s()$source_assignments[[t$id]]%||%'',selectize=FALSE),button('Save procedure assignment','assign_procedure',t$id))),
   if(length(t$blocked)&&!isTRUE(t$source_conflict)) tags$div(class='blocker',tags$strong(paste('Waiting on the',t$section,'lab mapping.')),tags$p('An administrator must complete this shared mapping before approval.'),button('Request mapping review','request_mapping',t$id),if(actor$role=='admin') button('Open lab mappings','mappings')),
   if(length(open)) uiOutput('progress'),
   lapply(open,function(k) field_cards(t,k)),
   if(length(saved)) tags$section(tags$h2(if(status(s(),t)=='Confirmed in OLSD') 'Confirmed in OLSD' else if(ready(t)) 'Approved' else if(can_approve(t)) 'Ready for approval' else 'Your saved choices'),lapply(saved,function(k) tags$div(class='saved',tags$h3(fields[[k]]),tags$div(class='comparison',value_block('In OLSD now',t$olsd[[k]],t$proposed[[k]]),value_block(if(same(t$proposed[[k]],t$olsd[[k]],k)) 'Kept' else 'After import',t$proposed[[k]],t$olsd[[k]])),tags$p(t$choices[[k]]$note),button(if(status(s(),t)=='Confirmed in OLSD') 'Edit' else 'Change','edit',field=k))),
    if(length(open_fields(t))) tags$p(paste('This test can be approved after every change has a choice. Waiting for:',paste(fields[open_fields(t)],collapse=', ')))),
   if(can_approve(t)) button(if(walking()&&origin()=='To approve') 'Approve and next' else 'Approve this test','approve',t$id,class='primary'),
   if(ready(t)) tagList(tags$p('Saving a new choice will withdraw this approval.'),button('Withdraw approval','withdraw',t$id)),
   if(length(other)) tags$section(if(length(open)||length(saved)) tags$h2('Other fields'),lapply(other,function(k) tags$div(class='other',tags$h3(fields[[k]]),tags$pre(t$olsd[[k]]),if(k=='labs') if(actor$role=='admin') button('Lab mappings','mappings') else tags$p('Laboratory names are managed centrally.') else button('Edit','edit',field=k)))),
   tags$details(tags$summary('History'),lapply(Filter(function(x) identical(x$id,t$id),s()$audit),function(x) tags$details(tags$summary(paste(x$at,x$actor,x$action)),tags$pre(jsonlite::toJSON(list(before=x$before,after=x$after),auto_unbox=TRUE,pretty=TRUE,null='null'))))),
   if(length(queue())) tags$div(class='walk',button('Previous','previous'),paste(match(t$id,queue()),'of',length(queue())),button('Next','next')))
 }
 downloadspage<-function() tagList(tags$h1('Downloads'),uiOutput('prepared_files'),lapply(rev(s()$exports),function(x) {
  remaining<-setdiff(names(x$rows),names(x$confirmed))
  tags$section(class='download-record',tags$h3(x$filename),tags$p(paste(x$at,'·',x$by)),
   if(length(x$retired)) tags$p(class='warning','Out of date. Do not import.'),
   lapply(names(x$rows),function(id) tags$p(paste(x$rows[[id]]$name,
    if(confirmed_row(x,id)) paste('Done · matched the catalog',x$confirmed[[id]]$at)
    else if(id%in%names(x$mismatches)) 'differs from this file. Review it in To review.'
    else if(length(x$retired)) 'Prepare a clean file for unconfirmed tests.'
    else 'Downloaded; import into OLSD.'))),
   if(length(remaining)&&!length(x$retired)&&!length(x$mismatches)) tags$p(if(length(x$confirmed)) paste('Nothing has reached OLSD yet for the unconfirmed tests:',paste(vapply(x$rows[remaining],function(r)r$name,character(1)),collapse='; ')) else 'Nothing has reached OLSD yet.'),
   if(!length(x$retired)) downloadButton(paste0('history_',x$id),'Download again'))
 }),tags$p('A matching snapshot confirms the values observed on that date; it does not prove real-time publication.'))
 output$page<-renderUI(switch(view(),worklist=worklist(),test=testpage(),
  snapshot=tagList(tags$h1('Update OLSD snapshot'),fileInput('snapshot_file','OLSD Excel export',accept='.xlsx'),uiOutput('snapshot_preview')),
  mappings=tagList(tags$h1('Lab mappings'),tags$p('Shared changes are applied to affected tests for review.'),tableOutput('mapping_table'),textInput('section','Epic section'),textInput('public_lab','Public laboratory name'),textInput('category','Approved category'),button('Save shared mapping','save_mapping')),
  downloads=downloadspage()))
 observeEvent(s(),{
  for(x in s()$exports) local({item<-x;output[[paste0('history_',item$id)]]<-downloadHandler(filename=function() item$filename,content=function(file) {
   require_role(actor);fresh<-store$read();current<-Filter(function(x) identical(x$id,item$id),fresh$exports)
   if(!length(current)||length(current[[1]]$retired)) fail('This file is out of date. Prepare a clean replacement.')
   paths<-pins::pin_download(board,item$artifact$pin)
   if(length(paths)!=1||digest::digest(file=paths[[1]],algo='sha256')!=item$artifact$hash) fail('Stored file failed integrity verification.')
   file.copy(paths[[1]],file,overwrite=TRUE)
  })})
 },ignoreInit=FALSE)
 output$mapping_table<-renderTable(s()$mappings)
 output$snapshot_preview<-renderUI(if(!is.null(upload())) tagList(tags$p(paste(nrow(upload()$rows),'tests; accepting this snapshot may return affected tests to review.')),tableOutput('upload_table'),button('Accept snapshot','accept_snapshot')))
 output$upload_table<-renderTable(if(!is.null(upload())) head(preview_olsd(s(),upload()$rows),50))
 observeEvent(input$snapshot_file,attempt(function(){require_role(actor,TRUE);r<-read_olsd(input$snapshot_file$datapath);upload(list(rows=r,reference=source_reference('OLSD',r)))}))
 output$progress<-renderUI({
  req(current());keys<-open_fields(current());n<-sum(vapply(keys,function(k) nzchar(input[[paste0('choice_',k)]]%||%drafts()[[test_id()]][[k]]$choice%||%''),logical(1)))
  if(length(keys)) tags$h2(paste(length(keys),'changes on this test ·',n,'of',length(keys),'chosen'))
 })
 output$savebar<-renderUI({
  if(view()!='test'&&!length(drafts())) return(NULL)
  advance<-walking()&&!is.null(current())&&all(vapply(open_fields(current()),function(k) nzchar(input[[paste0('choice_',k)]]%||%drafts()[[test_id()]][[k]]$choice%||%''),logical(1)))
  finish<-advance&&identical(tail(queue(),1),test_id())
  tags$div(class='savebar',button('Save','save',class=if(advance) '' else 'primary'),
   if(!finish) button('Save and exit','save_exit'),
   if(advance) button(if(finish) 'Save and finish' else 'Save and next','save_next',class='primary'),
   if(walking()&&!advance) tags$span('Choose an outcome for each change to enable Save and next.'),
   tags$span('Choosing never saves. Saving never approves.'))
 })
 output$prepared_files<-renderUI(tagList(lapply(seq_along(export_plan()),function(i) downloadButton(paste0('file_',i),paste('Download',export_plan()[[i]]$filename)))))
 observeEvent(input$route,{
  route<-strsplit(input$route,'/',fixed=TRUE)[[1]]
  if(length(route)>1&&route[[1]]=='test'&&route[[2]]%in%names(s()$tests)) {queue(names(rows()));navigate('test',route[[2]])}
  else if(route[[1]]%in%c('worklist','downloads','snapshot','mappings')) navigate(route[[1]])
 },ignoreInit=FALSE)
 observeEvent(input$command,attempt(function(){
  cmd<-input$command;id<-cmd$id;k<-cmd$field;a<-cmd$action
  if(a=='stay') {removeModal();return()}
  if(a=='discard') {drafts(list());session$sendCustomMessage('saved',TRUE);removeModal();fn<-action_pending();action_pending(NULL);if(!is.null(fn)) fn();return()}
  if(a=='save_continue') {save_all();removeModal();fn<-action_pending();action_pending(NULL);if(!is.null(fn)) fn();return()}
  if(a=='reload') {capture();if(length(drafts())) {showModal(modalDialog(title='Reload saved state?',tags$p('Keep your unsaved choices alongside the latest saved values. Review the new comparison before saving.'),footer=tagList(button('Stay','stay'),button('Reload and keep my choices','rebase'))))} else {s(store$read());revision(s()$revision)};return()}
  if(a=='rebase') {s(store$read());revision(s()$revision);removeModal();notify('Latest saved values loaded. Your unsaved choices remain for review.');return()}
  if(a%in%c('worklist','downloads','snapshot','mappings')) {navigate(a);return()}
  if(a=='tab') {capture();if(length(drafts())) {notify('Save or discard your choices before changing lists.');return()};tab(id);return()}
  if(a=='open') {origin(tab());queue(names(rows()));walking(FALSE);sole<-length(drafts())==1&&identical(names(drafts()),id);carried(if(sole) id else NULL);navigate('test',id,guard=!sole);return()}
  if(a=='back') {capture();sole<-identical(carried(),test_id())&&length(drafts())==1&&identical(names(drafts()),test_id());navigate('worklist',guard=!sole);carried(NULL);return()}
  if(a=='walk') {q<-intersect(names(rows()),selected());if(!length(q)) q<-names(rows());if(!length(q)) return();queue(q);walking(TRUE);walk_saved(character());origin(tab());navigate('test',q[[1]]);return()}
  if(a=='next') {step(1);return()};if(a=='previous') {step(-1);return()}
  if(a=='select_group') {ids<-names(Filter(function(t) section_for(t)==id,rows()));session$sendCustomMessage('selectRows',unique(c(selected(),ids)));return()}
  if(a=='select_all') {session$sendCustomMessage('selectRows',names(rows())%||%character());return()}
  if(a=='clear_selection') {session$sendCustomMessage('selectRows',character());return()}
  if(a=='edit') {capture();edits(unique(c(edits(),k)));return()}
  if(a=='cancel_edit') {capture();ds<-drafts();ds[[test_id()]][[k]]<-NULL;if(!length(ds[[test_id()]])) ds[[test_id()]]<-NULL;drafts(ds);edits(setdiff(edits(),k));return()}
  if(a%in%c('save','save_exit','save_next')) {save_all();if(a=='save_exit') navigate('worklist',guard=FALSE);if(a=='save_next') step(1);return()}
  if(grepl('^(inline|bulk)_',a)) {
   choice<-sub('^(inline|bulk)_','',a);ids<-if(grepl('^inline',a)) id else selected();ds<-drafts()
   for(tid in ids) {t<-s()$tests[[tid]];keys<-if(grepl('^inline',a)) k else intersect(open_fields(t),c('name','labs'));if(choice=='later') keys<-open_fields(t)
    for(f in keys) if(!f%in%t$blocked&&!is.null(t$epic[[f]])) ds[[tid]][[f]]<-list(choice=choice,note='',value=t$proposed[[f]])
   };drafts(ds);return()
  }
  if(a%in%c('approve','approve_selected')) {capture();if(length(drafts())) fail('Save choices before approving.');ids<-if(a=='approve') id else selected();write(function(st) approve_tests(st,ids,actor));notify('Selected tests approved. Approval does not upload or publish to OLSD.');if(walking()&&origin()=='To approve') step(1);return()}
  if(a%in%c('withdraw','send_selected')) {ids<-if(a=='withdraw') id else selected();write(function(st) send_back(st,ids,actor));notify('Returned to review. Earlier unconfirmed files are out of date; do not import them.');return()}
  if(a=='accept_snapshot') {capture();if(length(drafts())) fail('Save or discard choices before accepting a snapshot.');require_role(actor,TRUE);req(upload());u<-upload();store$claim(actor,token);snapshot_pin<-artifact_pin_name(cfg,'snapshot',u$reference$hash);if(!pins::pin_exists(board,snapshot_pin)) pin_write_versioned(board,u$rows,snapshot_pin);u$reference$pin<-snapshot_pin;u$reference$version<-pins::pin_meta(board,snapshot_pin)$local$version;write(function(st) apply_olsd(st,u$rows,u$reference,actor),TRUE);upload(NULL);notify('Snapshot accepted. Review affected tests.');return()}
  if(a=='apply_source') {capture();if(length(drafts())) fail('Save or discard choices before applying a source update.');src<-read_epic_pin(board,cfg$source_pin);write(function(st) apply_epic(st,src$rows,src$reference,actor));source_error('');notify('Latest Epic source applied.');return()}
  if(a=='assign_procedure') {
   capture();if(length(drafts())) fail('Save or discard choices before changing the procedure assignment.')
   require_role(actor,TRUE);src<-read_epic_pin(board,cfg$source_pin)
   write(function(st) assign_procedure(st,id,input$primary_procedure,src$rows,src$reference,actor),TRUE)
   notify('Procedure assignment saved. Review this entry’s source changes.');return()
  }
  if(a=='save_mapping') {
   capture();if(length(drafts())) fail('Save or discard choices before changing a shared mapping.');
   require_role(actor,TRUE);section<-trimws(input$section);lab<-trimws(input$public_lab);category<-trimws(input$category)
   if(!nzchar(section)||!nzchar(lab)||grepl('[;\r\n]',category)) fail('Supply an Epic section, a laboratory name, and one category.')
   src<-if(pins::pin_exists(board,cfg$source_pin)) read_epic_pin(board,cfg$source_pin) else NULL
   write(function(st) {st$mappings<-rbind(st$mappings[st$mappings$section!=section,,drop=FALSE],data.frame(section=section,lab=lab,category=category));st$categories<-unique(c(st$categories,category));st<-record(st,actor,'Saved shared mapping',section,after=list(lab=lab,category=category));if(!is.null(src)) st<-apply_epic(st,src$rows,src$reference,actor);st},TRUE);notify('Mapping saved. Affected tests require review.');return()
  }
  if(a=='request_mapping') {write(function(st) record(st,actor,'Requested administrator mapping review',id));notify('Request recorded in this test’s history.');return()}
  if(a=='prepare') {
   capture();if(length(drafts())||isTRUE(input$pilot_dirty)) fail('Save or discard unsaved choices before downloading.');require_role(actor);store$claim(actor,token)
   plans<-prepare_export(s(),selected());export_plan(plans)
   for(i in seq_along(plans)) local({j<-i;output[[paste0('file_',j)]]<-downloadHandler(filename=function() plans[[j]]$filename,content=function(file) {
    x<-plans[[j]];fresh<-store$read();if(fresh$revision!=revision()) fail('Saved state changed. Reload and prepare files again.')
    for(tid in names(x$rows)) if(!ready(fresh$tests[[tid]])||!identical(fresh$tests[[tid]]$approval$id,x$rows[[tid]]$approval_id)) fail('Approval changed.')
    pin<-artifact_pin_name(cfg,'export',x$id);pins::pin_upload(board,x$path,name=pin,versioned=TRUE)
    write(function(st) record_download(st,x,actor,list(pin=pin,hash=x$hash)))
    file.copy(x$path,file,overwrite=TRUE)
   },contentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
   navigate('downloads',guard=FALSE);return()
  }
 }))
}
shinyApp(ui,server)
