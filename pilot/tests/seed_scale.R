source('R/core.R');source('R/storage.R');source('R/sources.R')
if(config()$hosted) stop('Scale fixtures are forbidden on Connect.')
n<-1542L
rows<-data.frame(id=as.character(seq_len(n)),number=paste0('S',seq_len(n)),name=paste('Synthetic test',seq_len(n)),conditions='Synthetic conditions',labs='Main lab',categories='Chemistry',arup='',managed_by='Client',use_arup='No')
s<-apply_olsd(new_state(),rows,source_reference('Synthetic OLSD',rows),list(user='fixture'))
for(id in names(s$tests)) s$tests[[id]]$section<-'CHEM'
b<-pins::board_folder(Sys.getenv('OLSD_DATA_DIR'),versioned=TRUE);pin_write_versioned(b,s,'olsd-catalog-state')
