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
 required<-c('id','epic_id','name','sections')
 if(is.data.frame(d)&&all(c('id','epic_id')%in%names(d))) {
  duplicate<-unique(as.character(d$id[duplicated(d$id)]))
  if(length(duplicate)) fail(paste('OLSD IDs must be unique; check procedures linked to:',paste(duplicate,collapse=', ')))
 }
 d<-validate_rows(d,c(required,intersect(c('link_label','link_url'),names(d))),'id')
 if(any(!grepl('^[0-9]+$',d$id))||any(!nzchar(d$epic_id))||any(!nzchar(d$name))) fail('Epic rows require Procedure IDs, numeric OLSD IDs, and names.')
 for(proc in unique(d$epic_id)) {
  rows<-d[d$epic_id==proc,,drop=FALSE]
  if(length(unique(rows$name))>1||length(unique(rows$sections))>1) fail(paste('Conflicting source values for shared Epic procedure',proc))
 }
 d
}
# Expand each procedure into distinct OLSD entries. Labels are source context,
# never an inferred replacement for the OLSD name or a specimen mapping rule.
normalize_helix <- function(d) {
 required<-c('Procedure ID','Test Menu Links','Procedure Display Name','Authorized Lab Sections')
 d<-validate_rows(d,required,'Procedure ID')
 expanded<-list();linked<-rep(FALSE,nrow(d))
 for(i in seq_len(nrow(d))) {
  parts<-strsplit(d[['Test Menu Links']][[i]],';',fixed=TRUE)[[1]]
  records<-list()
  for(part in parts) {
   hits<-regmatches(part,gregexpr('/Tests/[0-9]+',part,ignore.case=TRUE))[[1]]
   if(!length(hits)) next
   label<-trimws(sub('https?://.*$','',part,ignore.case=TRUE))
   if(!grepl('https?://',part,ignore.case=TRUE)) label<-trimws(sub('/Tests/[0-9]+.*$','',part,ignore.case=TRUE))
   label<-sub('[:[:space:]]+$','',label)
   urls<-regmatches(part,gregexpr('https?://[^[:space:];<>]+',part,ignore.case=TRUE))[[1]]
   for(hit in unique(hits)) {
    id<-sub('/Tests/','',hit,ignore.case=TRUE)
    matching_urls<-urls[grepl(paste0('/Tests/',id,'([^0-9]|$)'),urls,ignore.case=TRUE)]
    old<-records[[id]]
    labels<-unique(c(old$link_label,label));labels<-labels[nzchar(labels)]
    records[[id]]<-list(id=id,epic_id=d[['Procedure ID']][[i]],name=d[['Procedure Display Name']][[i]],sections=d[['Authorized Lab Sections']][[i]],link_label=paste(labels,collapse=' | '),link_url=if(length(matching_urls)) matching_urls[[1]] else old$link_url%||%hit)
   }
  }
  linked[[i]]<-length(records)>0
  expanded<-c(expanded,unname(records))
 }
 if(!length(expanded)) fail('No Epic records contain an OLSD test link.')
 out<-do.call(rbind,lapply(expanded,function(x) as.data.frame(x,stringsAsFactors=FALSE)))
 rownames(out)<-NULL
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
