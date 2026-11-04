source('R/core.R');source('R/storage.R');source('R/sources.R')
cfg<-config()
for(p in c('shiny','pins','readxl','openxlsx','jsonlite','digest','filelock')) if(!requireNamespace(p,quietly=TRUE)) fail(paste('Missing package:',p))
if(cfg$hosted) {
 if(cfg$backend!='connect') fail('Connect deployments require Connect pins.')
 if(!nzchar(cfg$writer)) fail('Set OLSD_WRITER_USER to the designated operator.')
 if(!cfg$single_process) fail('Confirm a single worker and replica before enabling writes.')
}
board<-board_for(cfg);s<-pin_backend(board,cfg$pin,cfg$initialize)$read()
cat('State schema:',s$schema,'revision:',s$revision,'tests:',length(s$tests),'\n')
if(pins::pin_exists(board,cfg$source_pin)) {src<-read_epic_pin(board,cfg$source_pin);cat('Epic source rows:',nrow(src$rows),'fetched:',src$fetched_at,'\n')} else cat('Epic source not present; schedule and validate the source job before review.\n')
cat('Preflight reads succeeded. Write permissions and deployment topology require deployment validation.\n')
