# Read-only review export. No SQL, credentials, or procedure-level records included.
source('R/core.R');source('R/storage.R')
cfg<-config();board<-board_for(cfg);state<-pin_backend(board,cfg$pin,FALSE)$read()
values<-vapply(state$tests,function(t) t$olsd$labs%||%'',character(1))
labs<-as.data.frame(table(values),stringsAsFactors=FALSE);names(labs)<-c('Raw OLSD laboratory value','Number of OLSD entries')
labs<-labs[order(-labs[[2]],labs[[1]]),,drop=FALSE]
sections<-character()
if(pins::pin_exists(board,cfg$source_pin)) {
 payload<-pins::pin_read(board,cfg$source_pin)
 sections<-trimws(unlist(strsplit(payload$rows$sections,';',fixed=TRUE),use.names=FALSE));sections<-sort(unique(sections[nzchar(sections)]))
}
sheets<-list('Raw OLSD labs'=labs,'Epic sections'=data.frame('Epic section'=sections,check.names=FALSE),'Saved mappings'=state$mappings)
wb<-openxlsx::createWorkbook()
for(i in seq_along(sheets)) {
 openxlsx::addWorksheet(wb,names(sheets)[[i]]);openxlsx::writeData(wb,i,sheets[[i]])
 wb$worksheets_rels[[i]]<-wb$worksheets_rels[[i]][!grepl('relationships/(drawing|vmlDrawing)',wb$worksheets_rels[[i]])]
}
output<-file.path(getwd(),'lab-name-review.xlsx')
if(file.exists(output)) stop('lab-name-review.xlsx already exists. Rename it before exporting again.',call.=FALSE)
openxlsx::saveWorkbook(wb,output,overwrite=FALSE)
cat('Created:',output,'\nRaw formatting was preserved for review. No pin was changed.\n')
