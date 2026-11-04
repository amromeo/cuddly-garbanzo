config <- function() {
 hosted<-nzchar(Sys.getenv('CONNECT_SERVER'))||toupper(Sys.getenv('POSIT_PRODUCT'))=='CONNECT'||toupper(Sys.getenv('RSTUDIO_PRODUCT'))=='CONNECT'||tolower(Sys.getenv('OLSD_BACKEND'))=='connect'
 list(hosted=hosted,backend=Sys.getenv('OLSD_BACKEND',if(hosted) 'connect' else 'folder'),
 path=Sys.getenv('OLSD_DATA_DIR',file.path(getwd(),'local-pins')),pin=Sys.getenv('OLSD_STATE_PIN','olsd-catalog-state'),
 source_pin=Sys.getenv('OLSD_EPIC_PIN','olsd-epic-source'),writer=Sys.getenv('OLSD_WRITER_USER',if(hosted) '' else 'local-operator'),
 admins=trimws(strsplit(Sys.getenv('OLSD_ADMIN_USERS',if(hosted) '' else 'local-operator'),',',fixed=TRUE)[[1]]),
 single_process=identical(Sys.getenv('OLSD_SINGLE_PROCESS_CONFIRMED'),'true'),initialize=identical(Sys.getenv('OLSD_INITIALIZE'),'true'))
}
actor_for <- function(session,cfg) {
 user<-if(cfg$hosted) session$user%||%'' else 'local-operator'
 list(user=user,role=if(!nzchar(user)) 'reader' else if(user%in%cfg$admins) 'admin' else if(nzchar(user)&&identical(user,cfg$writer)) 'editor' else 'reader')
}
require_role <- function(actor,admin=FALSE) {
 if(!nzchar(actor$user)||!actor$role%in%(if(admin) 'admin' else c('editor','admin'))) fail(if(admin) 'Administrator access is required.' else 'Editor access is required.')
}
board_for <- function(cfg) {
 if(cfg$backend=='connect') return(pins::board_connect(auth='envvar'))
 if(cfg$hosted) fail('Hosted deployments must use Connect pins; local storage fallback is disabled.')
 pins::board_folder(cfg$path,versioned=TRUE)
}
pin_write_versioned <- function(board,value,name) {
 # Folder and Connect versions have second-resolution timestamps. Serialize
 # versions into distinct seconds so latest cannot select a sibling hash.
 if(pins::pin_exists(board,name)) {
  last<-substr(pins::pin_meta(board,name)$local$version,1,16)
  deadline<-Sys.time()+2
  while(format(Sys.time(),'%Y%m%dT%H%M%SZ',tz='UTC')<=last) {
   if(Sys.time()>deadline) fail('Pin version clock is ahead of this worker. Retry after checking clock synchronization.')
   Sys.sleep(0.05)
  }
 }
 pins::pin_write(board,value,name=name,type='rds',versioned=TRUE)
}
pin_backend <- function(board,name,initialize=FALSE) {
 list(read=function() {
  if(!pins::pin_exists(board,name)) {if(initialize) return(new_state());fail('Catalog state pin is missing. Initialize explicitly or restore a backup.')}
  validate_state(pins::pin_read(board,name))
 },write=function(s) {
  pin_write_versioned(board,validate_state(s),name)
  if(!identical(pins::pin_read(board,name),s)) fail('State verification failed. Reload before retrying.')
 })
}
new_store <- function(backend,cfg) {
 e<-new.env(parent=emptyenv());e$writer_session<-NULL;e$busy<-FALSE
 e$read<-backend$read
 e$claim<-function(actor,token) {
  require_role(actor)
  if(!identical(actor$user,cfg$writer)) fail('Only the designated pilot operator can make changes.')
  if(cfg$hosted&&!cfg$single_process) fail('Writes are disabled until the single-process Connect deployment is confirmed.')
  if(!is.null(e$writer_session)&&!identical(e$writer_session,token)) fail('Another browser session has editing control. Close it before taking control here.')
  e$writer_session<-token;invisible(TRUE)
 }
 e$release<-function(token) if(identical(token,e$writer_session)) e$writer_session<-NULL
 e$commit<-function(actor,token,revision,request_id,action) {
  e$claim(actor,token)
  if(e$busy) fail('A save is in progress. Please retry.')
  e$busy<-TRUE;on.exit({e$busy<-FALSE},add=TRUE)
  old<-backend$read()
  if(request_id%in%names(old$requests)) return(old)
  if(!identical(as.integer(revision),as.integer(old$revision))) fail('The catalog changed since you loaded it. Your unsaved choices remain; reload and review before saving.')
  next_state<-action(copy(old));next_state$revision<-old$revision+1L
  next_state$requests[[request_id]]<-list(actor=actor$user,at=now())
  backend$write(validate_state(next_state));next_state
 }
 e
}
# A process-lifetime local lock catches accidental extra workers on the same host.
# Connect must additionally be configured for a single process/replica for this pilot.
acquire_process_lock <- function(cfg) {
 path<-if(cfg$hosted) file.path('/tmp',paste0('olsd-writer-',digest::digest(list(Sys.getenv('CONNECT_SERVER'),cfg$pin),algo='sha256'),'.lock')) else file.path(cfg$path,'writer.lock')
 dir.create(dirname(path),recursive=TRUE,showWarnings=FALSE)
 lock<-filelock::lock(path,timeout=0)
 if(is.null(lock)) fail('Another application worker is running. The pins pilot requires one process.')
 lock
}

artifact_pin_name <- function(cfg,kind,identity) {
 if(!kind%in%c('snapshot','export')) fail('Unknown artifact kind.')
 # pins repeats a pin name in its directory and filename. Keep new artifact
 # names short enough for Windows; full identity remains in the state record.
 key<-digest::digest(list(namespace=cfg$pin,kind=kind,identity=identity),algo='sha256')
 scope<-if(cfg$backend=='connect'&&grepl('/',cfg$pin,fixed=TRUE)) paste0(sub('/[^/]+$','',cfg$pin),'/') else ''
 paste0(scope,if(kind=='snapshot') 'snap-' else 'file-',substr(key,1,24))
}
