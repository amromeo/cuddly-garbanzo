fields <- c(name='Test name', conditions='Unacceptable conditions', labs='Performing laboratories', categories='Search categories')
now <- function() format(Sys.time(), '%Y-%m-%dT%H:%M:%OS3Z', tz='UTC')
copy <- function(x) unserialize(serialize(x,NULL))
fail <- function(x) stop(x,call.=FALSE)
`%||%` <- function(a,b) if(is.null(a)) b else a
same <- function(a,b,k='name') {
  if(is.null(a)||is.null(b)) return(identical(a,b))
  normalize <- function(x) {x<-gsub('\r\n?','\n',x);if(k=='categories') sort(unique(trimws(strsplit(x,';',fixed=TRUE)[[1]]))) else x}
  identical(normalize(a),normalize(b))
}
new_state <- function() list(schema=1L,revision=0L,tests=list(),exports=list(),sources=list(),
  mappings=data.frame(section=character(),lab=character(),category=character()),
  categories=character(),audit=list(),requests=list())
validate_state <- function(s) {
  if(!is.list(s)||!identical(s$schema,1L)||!is.numeric(s$revision)||length(s$revision)!=1L) fail('Unsupported or invalid catalog state. Restore or migrate explicitly.')
  if(anyDuplicated(names(s$tests))) fail('Duplicate test identities.')
  for(t in s$tests) if(!all(names(fields)%in%names(t$olsd))||!all(names(fields)%in%names(t$proposed))) fail('Invalid test fields.')
  s
}
record <- function(s,actor,action,id='',before=NULL,after=NULL) {
 s$audit[[length(s$audit)+1L]]<-list(at=now(),actor=actor$user,action=action,id=id,before=before,after=after);s
}
changed <- function(t) names(fields)[vapply(names(fields),function(k) !same(t$olsd[[k]],t$proposed[[k]],k),logical(1))]
open_fields <- function(t) names(t$pending)
is_deferred <- function(t) any(vapply(t$choices,function(d) identical(d$choice,'later'),logical(1)))
can_approve <- function(t) length(changed(t))>0L&&!length(open_fields(t))&&!length(t$blocked)&&is.null(t$approval)
ready <- function(t) !is.null(t$approval)&&!isTRUE(t$approval$outdated)
confirmed_row <- function(x,id) !is.null(x$confirmed[[id]])
current_export <- function(s,t) {
 hits<-Filter(function(x) t$id%in%names(x$rows)&&!length(x$retired)&&identical(x$rows[[t$id]]$approval_id,t$approval$id),s$exports)
 if(length(hits)) hits[[length(hits)]] else NULL
}
status <- function(s,t) {
 if(isTRUE(t$source_issue)) return('Source issues')
 if(isTRUE(t$source_conflict)) return('To review')
 if(length(t$blocked)) return('Waiting on mapping')
 if(length(open_fields(t))) return(if(is_deferred(t)) 'Set aside' else 'To review')
 if(ready(t)) {x<-current_export(s,t);if(!is.null(x)) return(if(confirmed_row(x,t$id)) 'Confirmed in OLSD' else 'Downloaded');return('To download')}
 if(can_approve(t)) return('To approve')
 if(length(t$choices)) return('Kept wording')
 'Current'
}
retire <- function(s,id,reason) {
 for(i in seq_along(s$exports)) {
  x<-s$exports[[i]]
  if(id%in%names(x$rows)) {
   if(!confirmed_row(x,id)) x$retired[[id]]<-list(at=now(),reason=reason)
   else for(peer in setdiff(names(x$rows),names(x$confirmed))) x$retired[[peer]]<-list(at=now(),reason='This file contains an earlier confirmed version. Prepare a clean file for remaining tests.')
  }
  s$exports[[i]]<-x
 };s
}
new_test <- function(row) {
 vals<-as.list(row[names(fields)]); vals<-lapply(vals,as.character)
 list(id=as.character(row$id),number=as.character(row$number),epic_id='',section='',olsd=vals,epic=list(name=NULL,conditions=NULL,labs=NULL,categories=NULL),proposed=copy(vals),pending=list(),choices=list(),blocked=character(),approval=NULL,
 vendor=as.list(row[c('arup','managed_by','use_arup')]),sources=list(),saved_at=NULL)
}
# Commands contain choices, never authoritative approvals or whole replacement state.
apply_choices <- function(s,id,changes,actor) {
 t<-s$tests[[id]];if(is.null(t)) fail('Unknown test.')
 before<-copy(t)
 for(k in names(changes)) {
  if(!k%in%names(fields)) fail('Unknown field.')
  d<-changes[[k]];choice<-d$choice
  if(!choice%in%c('epic','olsd','custom','later')) fail('Choose an explicit outcome.')
  if(choice=='epic'&&(is.null(t$epic[[k]])||k%in%t$blocked)) fail('This Epic value is unavailable; resolve its mapping first.')
  if(choice=='custom'&&k=='labs') fail('Laboratory names are managed through administrator mappings.')
  if(choice=='custom'&&k=='categories') {
    selected<-trimws(strsplit(d$value,';',fixed=TRUE)[[1]])
    if(any(!selected[nzchar(selected)]%in%s$categories)) fail('Choose approved categories only.')
  }
  oldchoice<-t$choices[[k]]
  if(choice=='later') {
   if(is.null(t$epic[[k]])||same(t$epic[[k]],t$olsd[[k]],k)) fail('This field has no Epic difference to set aside.')
   previous<-if(!is.null(oldchoice)&&oldchoice$choice!='later') list(value=t$proposed[[k]],decision=oldchoice) else oldchoice$previous
   t$pending[[k]]<-t$pending[[k]]%||%list(source='Epic',before=t$olsd[[k]],after=t$epic[[k]])
   t$proposed[[k]]<-t$olsd[[k]]
  } else {
   previous<-NULL
   value<-switch(choice,epic=t$epic[[k]],olsd=t$olsd[[k]],custom=d$value)
   if(!is.character(value)||length(value)!=1||is.na(value)||nchar(value)>32000) fail('Enter a valid field value (at most 32,000 characters).')
   if(k=='name'&&!nzchar(trimws(value))) fail('Test name is required.')
   t$proposed[[k]]<-value;t$pending[[k]]<-NULL
  }
  note<-d$note%||%'';if(!is.character(note)||length(note)!=1||nchar(note)>2000) fail('Note is too long.')
  t$choices[[k]]<-list(choice=choice,note=note,at=now(),by=actor$user,epic=t$epic[[k]],olsd=t$olsd[[k]],previous=previous)
 }
 if(!identical(before,t)) {s<-retire(s,id,'The saved choice changed.');t$approval<-NULL;t$saved_at<-now()}
 s$tests[[id]]<-t;record(s,actor,'Saved choices',id,before,t)
}
approve_tests <- function(s,ids,actor) {
 if(!length(ids)||any(!ids%in%names(s$tests))) fail('Select tests to approve.')
 if(any(!vapply(s$tests[ids],can_approve,logical(1)))) fail('Every selected test must have all choices saved and all mappings resolved.')
 for(id in ids) {t<-s$tests[[id]];t$approval<-list(id=digest::digest(list(id,now(),s$revision,runif(1)),algo='sha256'),by=actor$user,at=now(),number=t$number,olsd=copy(t$olsd),epic=copy(t$epic),proposed=copy(t$proposed),choices=copy(t$choices),vendor=copy(t$vendor),sources=copy(t$sources),outdated=FALSE);s$tests[[id]]<-t;s<-record(s,actor,'Approved',id,after=t$approval)};s
}
send_back <- function(s,ids,actor) {
 for(id in ids) {t<-s$tests[[id]];if(is.null(t)) fail('Unknown test.');s<-retire(s,id,'Approval withdrawn or update sent back.');t$approval<-NULL
 for(k in changed(t)) t$pending[[k]]<-list(source='Saved wording',before=t$olsd[[k]],after=t$proposed[[k]],saved=t$proposed[[k]])
 s$tests[[id]]<-t;s<-record(s,actor,'Sent back to review',id)};s
}
# All expected rows are captured before modifying any test, avoiding order-dependent results.
apply_olsd <- function(s,rows,source,actor) {
 frozen<-copy(s);observed<-rows$id
 for(i in seq_len(nrow(rows))) {
  r<-rows[i,,drop=FALSE];id<-r$id
  if(is.null(s$tests[[id]])) {s$tests[[id]]<-new_test(r);s$tests[[id]]$sources$olsd<-source;next}
  t<-s$tests[[id]];x<-current_export(frozen,t);expected<-if(!is.null(x)) x$rows[[id]] else NULL
  for(k in names(fields)) {
   value<-as.character(r[[k]])
   if(!same(value,t$olsd[[k]],k)) {
    previous<-t$olsd[[k]];t$olsd[[k]]<-value
    if(!is.null(expected)&&k%in%expected$fields&&same(value,expected$values[[k]],k)) {
     t$pending[[k]]<-NULL
    } else {
     if(!k%in%names(t$choices)) t$proposed[[k]]<-value
     t$pending[[k]]<-list(source='OLSD',before=previous,after=value,saved=t$proposed[[k]])
     if(!is.null(t$approval)) t$approval$outdated<-TRUE
    }
   }
  }
  vendor<-as.list(r[c('arup','managed_by','use_arup')]);vendor<-lapply(vendor,as.character)
  if((!identical(t$vendor,vendor)||!identical(t$number,as.character(r$number)))&&!is.null(t$approval)) {t$approval$outdated<-TRUE;t$pending$name<-list(source='OLSD control columns',before=t$olsd$name,after=t$olsd$name)}
  t$vendor<-vendor;t$number<-as.character(r$number);t$sources$olsd<-source;s$tests[[id]]<-t
 }
 for(i in seq_along(s$exports)) {
  x<-s$exports[[i]]
  for(id in intersect(names(x$rows),observed)) {
   row<-x$rows[[id]];t<-s$tests[[id]]
   matches<-all(vapply(row$fields,function(k) if(k=='categories') all(trimws(strsplit(row$values[[k]],';',fixed=TRUE)[[1]])%in%trimws(strsplit(t$olsd[[k]],';',fixed=TRUE)[[1]])) else same(row$values[[k]],t$olsd[[k]],k),logical(1)))
   matches<-matches&&identical(t$number,row$number)&&identical(t$vendor,row$vendor)
   x$comparisons[[id]]<-list(at=now(),matches=matches,source=source)
   # Retired files remain retired even when their rejected value appears later.
   eligible<-!length(x$retired)&&!is.null(t$approval)&&identical(row$approval_id,t$approval$id)
   if(matches&&eligible) {if(!length(open_fields(t))&&identical(t$epic,t$approval$epic)&&identical(t$vendor,t$approval$vendor)) t$approval$outdated<-FALSE;x$confirmed[[id]]<-x$confirmed[[id]]%||%list(at=now(),source=source);x$mismatches[[id]]<-NULL}
   if(!matches&&eligible&&!confirmed_row(x,id)) {
    x$mismatches[[id]]<-list(at=now(),source=source)
    for(k in row$fields) if(!same(row$values[[k]],t$olsd[[k]],k)) t$pending[[k]]<-list(source='File comparison',before=row$values[[k]],after=t$olsd[[k]],saved=t$proposed[[k]])
    t$approval$outdated<-TRUE
   }
   s$tests[[id]]<-t
  };s$exports[[i]]<-x
 }
 s$sources$olsd<-source;record(s,actor,'Accepted OLSD snapshot',after=source)
}
apply_epic <- function(s,rows,source,actor) {
 rows<-validate_epic(rows)
 s$source_assignments<-s$source_assignments%||%list()
 for(id in unique(rows$id)) {
  group<-rows[rows$id==id,,drop=FALSE];t<-s$tests[[id]];if(is.null(t)) next
  previous_links<-t$linked_procedures
  t$linked_procedures<-group
  primary<-s$source_assignments[[id]]
  normalized_sections<-vapply(strsplit(group$sections,';',fixed=TRUE),function(x) paste(sort(unique(trimws(x))),collapse=';'),character(1))
  candidates<-if(!is.null(primary)&&primary%in%group$epic_id) group[group$epic_id==primary,,drop=FALSE] else group
  t$source_issue<-any(!nzchar(trimws(candidates$name)))
  conflict<-t$source_issue||(!is.null(primary)&&!primary%in%group$epic_id)||(is.null(primary)&&(length(unique(group$name))>1||length(unique(normalized_sections))>1))
  if(conflict) {
   t$source_conflict<-TRUE;t$blocked<-c('name','labs','categories');t$epic_id<-paste(group$epic_id,collapse=', ');t$section<-paste(unique(group$sections),collapse=' | ');t$sources$epic<-source
   for(k in c('name','labs','categories')) {t$epic[k]<-list(NULL);t$pending[[k]]<-list(source='Procedure assignment',before=t$olsd[[k]],after=NULL,saved=t$proposed[[k]])}
   if(!is.null(t$approval)) t$approval$outdated<-TRUE
   if(!identical(previous_links,group)) s<-retire(s,id,'Linked Epic procedures need an administrator source assignment.')
   s$tests[[id]]<-t;next
  }
  r<-if(!is.null(primary)) group[group$epic_id==primary,,drop=FALSE] else group[1,,drop=FALSE]
  if(isTRUE(t$source_conflict)&&!is.null(t$approval)) t$approval<-NULL
  t$source_conflict<-FALSE
  sections<-trimws(strsplit(r$sections,';',fixed=TRUE)[[1]]);m<-s$mappings[match(sections,s$mappings$section),,drop=FALSE]
  blocked<-!length(sections)||anyNA(m$lab)||any(!nzchar(m$lab))
  vals<-list(name=r$name,labs=if(blocked) NULL else paste(unique(m$lab),collapse='\n'),categories=if(blocked) NULL else paste(unique(m$category[nzchar(m$category)]),collapse=';'))
  t$shared_procedure<-any(vapply(group$epic_id,function(p) length(unique(rows$id[rows$epic_id==p]))>1,logical(1)));t$link_label<-r$link_label%||%'';t$link_url<-r$link_url%||%'';t$sources$epic<-source;t$epic_id<-r$epic_id;t$section<-r$sections;t$blocked<-if(blocked) 'labs' else character()
  for(k in names(vals)) if(identical(t$pending[[k]]$source,'Procedure assignment')&&same(vals[[k]],t$proposed[[k]],k)) t$pending[[k]]<-NULL
  for(k in names(vals)) {
   v<-vals[[k]]
   if(!same(v,t$epic[[k]],k)) {
    old<-t$epic[[k]];t$epic[k]<-list(v)
    if(!blocked&&identical(t$pending[[k]]$source,'Lab mapping')&&same(v,t$proposed[[k]],k)) t$pending[[k]]<-NULL
    if(!same(v,t$proposed[[k]],k)||!is.null(t$approval)) {
     t$pending[[k]]<-list(source='Epic',before=old,after=v,saved=t$proposed[[k]])
     if(!is.null(t$approval)) t$approval$outdated<-TRUE
     s<-retire(s,id,'Epic changed after this file was prepared.')
    }
   }
  }
  if(blocked) t$pending$labs<-list(source='Lab mapping',before=t$olsd$labs,after=NULL)
  s$tests[[id]]<-t
 }
 for(id in setdiff(names(s$tests),unique(rows$id))) {
  t<-s$tests[[id]]
  if(!is.null(t$linked_procedures)&&nrow(t$linked_procedures)) {
   t$linked_procedures<-rows[FALSE,,drop=FALSE];t$source_conflict<-TRUE;t$blocked<-c('name','labs','categories');t$sources$epic<-source
   for(k in t$blocked) {t$epic[k]<-list(NULL);t$pending[[k]]<-list(source='Procedure assignment',before=t$olsd[[k]],after=NULL,saved=t$proposed[[k]])}
   if(!is.null(t$approval)) t$approval$outdated<-TRUE
   s<-retire(s,id,'This OLSD entry no longer has a linked Epic procedure.');s$tests[[id]]<-t
  }
 }
 s$sources$epic<-source;record(s,actor,'Applied Epic source',after=source)
}

display_date <- function(value) {
 if(is.null(value)||!nzchar(value)) return('Not recorded')
 time<-as.POSIXct(value,format='%Y-%m-%dT%H:%M:%OSZ',tz='UTC')
 if(is.na(time)) return('Not recorded')
 days<-max(0,floor(as.numeric(difftime(Sys.time(),time,units='days'))))
 paste0(format(time,'%b %d, %Y, %I:%M %p %Z',tz='America/New_York'),' (',if(days==0) 'today' else paste(days,if(days==1) 'day old' else 'days old'),')')
}

assign_procedure <- function(s,id,procedure,rows,source,actor) {
 require_role(actor,TRUE)
 if(!id%in%names(s$tests)||!procedure%in%rows$epic_id[rows$id==id]) fail('Choose a procedure currently linked to this OLSD entry.')
 selected<-rows[rows$id==id & rows$epic_id==procedure,,drop=FALSE]
 if(!nzchar(trimws(selected$name))) fail('This procedure has no Epic display name. Correct the warehouse source or choose a complete linked procedure.')
 previous<-s$source_assignments[[id]]
 s$source_assignments[[id]]<-procedure
 s<-retire(s,id,'The primary Epic procedure assignment changed.');s$tests[[id]]$approval<-NULL
 s<-record(s,actor,'Assigned primary Epic procedure',id,before=previous,after=procedure)
 apply_epic(s,rows,source,actor)
}
