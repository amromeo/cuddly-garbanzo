# Schedule nightly on Connect; this job never writes editorial state.
source('R/core.R');source('R/storage.R');source('R/sources.R')
cfg<-config();board<-board_for(cfg)
tryCatch({
 upstream<-Sys.getenv('OLSD_HELIX_PIN')
 if(nzchar(upstream)) {
  meta<-pins::pin_meta(board,upstream);raw<-pins::pin_read(board,upstream,version=meta$local$version)
 } else {
  if(!file.exists('jobs/helix_direct.R')) fail('Configure OLSD_HELIX_PIN, or explicitly deploy the institutional Helix adapter.')
  source('jobs/helix_direct.R');raw<-read_helix_sql()
 }
 normalized<-normalize_helix(as.data.frame(raw,check.names=FALSE))
 payload<-list(schema=1L,fetched_at=now(),rows=normalized$rows,excluded=normalized$excluded,issues=normalized$issues,hash=digest::digest(normalized$rows,algo='sha256'))
 pins::pin_write(board,payload,name=cfg$source_pin,type='rds',versioned=TRUE)
 pins::pin_write(board,list(ok=TRUE,at=now(),rows=nrow(payload$rows)),name=paste0(cfg$source_pin,'-status'),type='rds',versioned=TRUE)
},error=function(e){
 try(pins::pin_write(board,list(ok=FALSE,at=now(),message='Source refresh failed. See restricted Connect job logs; last successful source retained.'),name=paste0(cfg$source_pin,'-status'),type='rds',versioned=TRUE),silent=TRUE);stop(e)
})
