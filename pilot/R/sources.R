olsd_columns <- c(id='Test Id',number='Test Number',name='Test Name',conditions='Unacceptable Conditions',labs='Performing Lab',categories='Test Search Categories',arup='ARUP Test Number',managed_by='Test Managed By',use_arup='Use ARUP Test Name')
validate_rows <- function(d,required,identity) {
 if(!is.data.frame(d)||anyDuplicated(names(d))||!all(required%in%names(d))) fail(paste('Required unique columns:',paste(required,collapse=', ')))
 d<-d[,required,drop=FALSE];d[]<-lapply(d,function(x) {x<-as.character(x);x[is.na(x)]<-'';enc2utf8(x)})
 if(!nrow(d)||any(!nzchar(trimws(d[[identity]])))||anyDuplicated(d[[identity]])) fail('The snapshot must have unique, nonblank test identities.')
 if(any(vapply(d,function(x) any(nchar(x)>32000),logical(1)))) fail('A value exceeds the Excel field size limit.')
 d
}
read_olsd <- function(path) {
 sheets<-readxl::excel_sheets(path);sheet<-if('Tests'%in%sheets) 'Tests' else sheets[[1]]
 d<-as.data.frame(readxl::read_excel(path,sheet=sheet,col_types='text',.name_repair='minimal'),check.names=FALSE)
 d<-validate_rows(d,unname(olsd_columns),'Test Id');names(d)<-names(olsd_columns)
 if(any(!grepl('^[0-9]+$',d$id))) fail('OLSD Test Id must contain digits only.')
 if(any(!nzchar(trimws(d$name)))) fail('Every test requires a name.')
 d
}
validate_epic <- function(d) {
 d<-validate_rows(d,c('id','epic_id','name','sections'),'id')
 if(any(!grepl('^[0-9]+$',d$id))||any(!nzchar(d$epic_id))||anyDuplicated(d$epic_id)||any(!nzchar(d$name))) fail('Epic rows require unique Procedure IDs, numeric OLSD IDs, and names.')
 d
}
# Explicit normalization boundary for the existing Helix report. Unlinked records
# are retained in the source's excluded table, never guessed into the catalog.
normalize_helix <- function(d) {
 required<-c('Procedure ID','Test Menu Links','Procedure Display Name','Authorized Lab Sections')
 d<-validate_rows(d,required,'Procedure ID')
 links<-d[['Test Menu Links']]
 matches<-regmatches(links,gregexpr('/Tests/[0-9]+',links))
 ids<-vapply(matches,function(x) {if(length(unique(x))>1) fail('An Epic record links to multiple OLSD identities.');if(!length(x)) '' else sub('/Tests/','',x[[1]],fixed=TRUE)},character(1))
 linked<-nzchar(ids)
 if(!any(linked)) fail('No Epic records contain an OLSD test link.')
 out<-data.frame(id=ids[linked],epic_id=d[['Procedure ID']][linked],name=d[['Procedure Display Name']][linked],sections=d[['Authorized Lab Sections']][linked],stringsAsFactors=FALSE)
 list(rows=validate_epic(out),excluded=d[!linked,,drop=FALSE])
}
source_reference <- function(kind,rows,version=NULL) list(kind=kind,at=now(),version=version,hash=digest::digest(rows,algo='sha256'))
read_epic_pin <- function(board,name) {
 metadata<-pins::pin_meta(board,name)
 payload<-pins::pin_read(board,name,version=metadata$local$version)
 if(!is.list(payload)||is.null(payload$rows)||is.null(payload$fetched_at)) fail('The Epic source pin does not match the pilot source contract.')
 payload$rows<-validate_epic(payload$rows)
 payload$reference<-source_reference('Epic',payload$rows,metadata$local$version)
 payload$reference$at<-payload$fetched_at;payload
}
preview_olsd <- function(s,rows) {
 data.frame(id=rows$id,name=rows$name,result=vapply(seq_len(nrow(rows)),function(i) {
  t<-s$tests[[rows$id[[i]]]];if(is.null(t)) return('New test')
  changes<-names(fields)[!vapply(names(fields),function(k) same(t$olsd[[k]],rows[[k]][[i]],k),logical(1))]
  if(length(changes)) paste(unname(fields[changes]),collapse=', ') else 'Unchanged'
 },character(1)))
}
