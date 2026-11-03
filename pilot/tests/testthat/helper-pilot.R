for(f in c('core','storage','sources','exports')) source(file.path('..','..','R',paste0(f,'.R')))
admin<-list(user='operator',role='admin');editor<-list(user='operator',role='editor')
fixture<-function(n=3) {
 d<-data.frame(id=as.character(seq_len(n)),number=paste0('T',seq_len(n)),name=paste('Test',seq_len(n)),conditions='Current conditions',labs='Main lab',categories='Chemistry',arup='',managed_by='Client',use_arup='No')
 s<-apply_olsd(new_state(),d,source_reference('OLSD',d),admin)
 s$mappings<-data.frame(section='CHEM',lab='Main lab',category='Chemistry');s$categories<-'Chemistry'
 e<-data.frame(id=d$id,epic_id=paste0('P',d$id),name=paste('New name',seq_len(n)),sections='CHEM')
 for(id in names(s$tests)) {s$tests[[id]]$epic$labs<-'Main lab';s$tests[[id]]$epic$categories<-'Chemistry'}
 s<-apply_epic(s,e,source_reference('Epic',e),admin);attr(s,'rows')<-d;attr(s,'epic')<-e;s
}
accept_names<-function(s) {for(id in names(s$tests)) s<-apply_choices(s,id,list(name=list(choice='epic',note='Reviewed')),editor);s}
exported_fixture<-function(n=5) {
 s<-approve_tests(accept_names(fixture(n)),as.character(seq_len(n)),editor)
 x<-prepare_export(s,as.character(seq_len(n)))[[1]];record_download(s,x,editor,list(pin='test',hash=x$id))
}
mem_backend<-function() {e<-new.env();e$s<-new_state();e$fail<-FALSE;list(env=e,read=function() copy(e$s),write=function(s) {if(e$fail) fail('Simulated persistence failure');e$s<-copy(s)})}
