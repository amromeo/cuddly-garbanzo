export_groups <- function(s,ids) {
 if(!length(ids)||any(!ids%in%names(s$tests))) fail('Select approved tests.')
 if(any(!vapply(s$tests[ids],ready,logical(1)))) fail('Only current approved versions can be downloaded.')
 split(ids,vapply(s$tests[ids],function(t) paste(unique(c('name',changed(t))),collapse='|'),character(1)))
}
export_frame <- function(s,ids,selected_fields) {
 rows<-lapply(s$tests[ids],function(t) {
  a<-t$approval
  values<-list('Test Number'=a$number,'Test Name'=a$proposed$name,'ARUP Test Number'=a$vendor$arup,'Test Managed By'=a$vendor$managed_by,'Use ARUP Test Name'=a$vendor$use_arup,'Test Id'=t$id)
  for(k in setdiff(selected_fields,'name')) values[[olsd_columns[[k]]]]<-a$proposed[[k]]
  as.data.frame(values,check.names=FALSE,stringsAsFactors=FALSE)
 });do.call(rbind,rows)
}
prepare_export <- function(s,ids,dir=tempdir()) {
 groups<-export_groups(s,ids);result<-list()
 for(group in groups) {
  fs<-unique(c('name',changed(s$tests[[group[[1]]]])))
  stamp<-format(Sys.time(),'%Y-%m-%d_%H%M',tz='America/New_York')
  title<-if(length(group)==1) gsub('[^A-Za-z0-9_-]','_',s$tests[[group]]$number) else paste0(length(group),'_tests')
  base<-paste0('OLSD_',title,'_',stamp);filename<-paste0(base,'.xlsx');i<-1
  used<-c(vapply(s$exports,function(x) x$filename,character(1)),vapply(result,function(x) x$filename,character(1)))
  while(filename%in%used){i<-i+1;filename<-paste0(base,'_',i,'.xlsx')}
  path<-file.path(dir,filename)
  wb<-openxlsx::createWorkbook();openxlsx::addWorksheet(wb,'Tests');openxlsx::writeData(wb,'Tests',export_frame(s,group,fs));# Data-only workbooks must not reference absent drawings (openxlsx 4.2.9 defaults).
  wb$worksheets_rels[[1]]<-wb$worksheets_rels[[1]][!grepl('relationships/(drawing|vmlDrawing)',wb$worksheets_rels[[1]])]
  openxlsx::saveWorkbook(wb,path,overwrite=TRUE)
  hash<-digest::digest(file=path,algo='sha256')
  rows<-lapply(s$tests[group],function(t) list(id=t$id,name=t$olsd$name,number=t$approval$number,vendor=copy(t$approval$vendor),fields=fs,values=copy(t$approval$proposed),approval_id=t$approval$id))
  result[[length(result)+1L]]<-list(id=digest::digest(list(hash,now(),runif(1)),algo='sha256'),hash=hash,filename=filename,path=path,rows=rows,fields=fs,confirmed=list(),comparisons=list(),retired=list(),mismatches=list())
 };result
}
record_download <- function(s,x,actor,artifact) {
 if(any(vapply(s$exports,function(y) identical(y$id,x$id),logical(1)))) return(s)
 for(id in names(x$rows)) if(!ready(s$tests[[id]])||!identical(s$tests[[id]]$approval$id,x$rows[[id]]$approval_id)) fail('Approval changed. Prepare a new file.')
 x$path<-NULL;x$at<-now();x$by<-actor$user;x$artifact<-artifact
 s$exports[[length(s$exports)+1L]]<-x;record(s,actor,'Download initiated',after=list(file=x$filename,hash=x$id))
}
