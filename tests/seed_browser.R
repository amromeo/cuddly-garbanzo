# Synthetic fixture generator. Output directory is supplied by the test runner.
source('R/core.R');source('R/storage.R');source('R/sources.R')
if(config()$hosted) stop('Browser fixtures are forbidden on Connect.')
board<-pins::board_folder(Sys.getenv('OLSD_DATA_DIR'),versioned=TRUE)
d<-data.frame(id=c('1','2'),number=c('T1','T2'),name=c('Test 1','Test 2'),conditions='Current conditions',labs='Main lab',categories='Chemistry',arup='',managed_by='Client',use_arup='No')
names(d)<-unname(olsd_columns[names(d)]);openxlsx::write.xlsx(list(Tests=d),file.path(Sys.getenv('OLSD_DATA_DIR'),'snapshot.xlsx'))
pin_write_versioned(board,list(rows=data.frame(id=c('1','2','2'),epic_id=c('P1','P1','P2'),name=c('New name 1','New name 1','New name 2'),sections='CHEM',link_label=c('Blood','CSF','Alternate source')),fetched_at=now()),'olsd-epic-source')
