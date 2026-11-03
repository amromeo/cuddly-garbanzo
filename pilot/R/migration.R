# Pure conversion: callers save a preview/candidate, never overwrite the live pin.
migrate_legacy <- function(old,actor) {
 if(!old$schema_version%in%c(7L,8L)||!is.data.frame(old$tests)||!is.data.frame(old$fields)) fail('Only the supplied schema 7/8 catalog-state format is supported. Inspect other schemas before migrating.')
 map<-c(id='test_id',number='test_number',name='baseline_test_name',conditions='baseline_unacceptable_conditions',labs='baseline_performing_lab',categories='baseline_test_search_categories',arup='arup_test_number',managed_by='test_managed_by',use_arup='use_arup_test_name')
 if(!all(unname(map)%in%names(old$tests))) fail('Legacy tests are missing baseline columns.')
 rows<-old$tests[,unname(map),drop=FALSE];names(rows)<-names(map);rows<-validate_rows(rows,names(map),'id')
 s<-apply_olsd(new_state(),rows,source_reference('Legacy baseline',rows),actor)
 if(is.data.frame(old$lab_mapping)&&nrow(old$lab_mapping)) {
  m<-old$lab_mapping[old$lab_mapping$include%in%TRUE,,drop=FALSE]
  if(anyDuplicated(m$epic_lab_section)) fail('Resolve duplicate legacy lab sections before migration; no mappings were guessed.')
  s$mappings<-data.frame(section=m$epic_lab_section,lab=m$public_performing_lab,category=m$search_category)
 }
 if(is.data.frame(old$categories)) s$categories<-old$categories$label[old$categories$status=='ACTIVE']
 report<-list()
 for(i in seq_len(nrow(old$tests))) {
  r<-old$tests[i,,drop=FALSE];id<-r$test_id;t<-s$tests[[id]]
  if('epic_procedure_id'%in%names(r)) t$epic_id<-r$epic_procedure_id
  if('epic_display_name'%in%names(r)) t$epic$name<-r$epic_display_name
  if('epic_authorized_lab_sections'%in%names(r)) t$section<-r$epic_authorized_lab_sections
  desired<-list()
  if('name_override'%in%names(r)&&!is.na(r$name_override)&&nzchar(r$name_override)) desired$name<-r$name_override
  f<-old$fields[old$fields$test_id==id & old$fields$enabled%in%TRUE,,drop=FALSE]
  for(j in seq_len(nrow(f))) {
   k<-names(olsd_columns)[match(f$field_name[[j]],olsd_columns)]
   if(length(k)&&!is.na(k)&&k%in%names(fields)) desired[[k]]<-f$value[[j]]
  }
  if(is.data.frame(old$test_categories)) {
   cats<-old$test_categories[old$test_categories$test_id==id & old$test_categories$enabled%in%TRUE,,drop=FALSE]
   if(nrow(cats)) {
    labels<-if('category_id'%in%names(cats)) old$categories$label[match(cats$category_id,old$categories$category_id)] else cats$category
    if(anyNA(labels)||any(!labels%in%s$categories)) fail(paste('Resolve category identities for',id,'before migration.'))
    desired$categories<-paste(unique(c(strsplit(t$olsd$categories,';',fixed=TRUE)[[1]],labels)),collapse=';')
   }
  }
  for(k in names(desired)) {
   t$proposed[[k]]<-desired[[k]]
   t$pending[[k]]<-list(source='Legacy migration',before=t$olsd[[k]],after=desired[[k]],saved=desired[[k]])
   report[[length(report)+1L]]<-data.frame(id=id,field=k,in_olsd=t$olsd[[k]],saved_wording=desired[[k]],result='Requires review; no approval migrated')
  }
  t$approval<-NULL;s$tests[[id]]<-t
 }
 # Preserve disabled field values, old decisions, approvals, exports, and aliases
 # as an archive, never as active workflow state.
 s$legacy_archive<-copy(old)
 s<-record(s,actor,'Prepared legacy migration',after=list(source_schema=old$schema_version,tests=nrow(rows)))
 list(state=validate_state(s),report=if(length(report)) do.call(rbind,report) else data.frame())
}
