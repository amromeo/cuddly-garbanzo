source(file.path('..','..','R','migration.R'))
test_that('legacy wording survives without promoting historical approvals', {
 s<-fixture(1);d<-attr(s,'rows');map<-c(id='test_id',number='test_number',name='baseline_test_name',conditions='baseline_unacceptable_conditions',labs='baseline_performing_lab',categories='baseline_test_search_categories',arup='arup_test_number',managed_by='test_managed_by',use_arup='use_arup_test_name');names(d)<-unname(map[names(d)])
 d$name_override<-'My legacy name'
 old<-list(schema_version=8L,tests=d,fields=data.frame(test_id='1',field_name='Unacceptable Conditions',value='Legacy conditions',enabled=TRUE),approvals=data.frame(test_id='1',approved_at='old'))
 result<-migrate_legacy(old,admin)
 expect_equal(result$state$tests[['1']]$proposed$name,'My legacy name')
 expect_equal(result$state$tests[['1']]$proposed$conditions,'Legacy conditions')
 expect_null(result$state$tests[['1']]$approval);expect_length(result$state$tests[['1']]$pending,2)
 expect_identical(result$state$legacy_archive,old);expect_equal(nrow(result$report),2)
})
