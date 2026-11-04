test_that('choice, save, approval and export are distinct', {
 s<-fixture();expect_false(can_approve(s$tests[['1']]))
 s<-apply_choices(s,'1',list(name=list(choice='epic',note='Reviewed')),editor)
 expect_true(can_approve(s$tests[['1']]));expect_null(s$tests[['1']]$approval);expect_length(s$exports,0)
 s<-approve_tests(s,'1',editor);expect_true(ready(s$tests[['1']]));expect_error(approve_tests(s,'1',editor))
 plans<-prepare_export(s,'1');expect_length(s$exports,0)
 d<-readxl::read_excel(plans[[1]]$path,col_types='text');expect_equal(d[['Test Name']],'New name 1');expect_equal(d[['Test Managed By']],'Client');expect_equal(d[['Test Id']],'1')
 s<-record_download(s,plans[[1]],editor,list(pin='test'));expect_length(s$exports,1)
})
test_that('multiple fields remain open until explicitly decided', {
 s<-fixture(1);s$tests[['1']]$epic$labs<-'New lab';s$tests[['1']]$pending$labs<-list(source='Epic')
 s<-apply_choices(s,'1',list(name=list(choice='epic')),editor);expect_false(can_approve(s$tests[['1']]))
 s<-apply_choices(s,'1',list(labs=list(choice='later',note='Ask lab')),editor)
 expect_true(is_deferred(s$tests[['1']]));expect_false(can_approve(s$tests[['1']]));expect_error(approve_tests(s,'1',editor),'Every')
 s<-apply_choices(s,'1',list(labs=list(choice='olsd')),editor);expect_true(can_approve(s$tests[['1']]))
})
test_that('custom wording survives deferral', {
 s<-fixture(1);s<-apply_choices(s,'1',list(name=list(choice='custom',value='Careful wording',note='Clinical reason')),editor)
 s<-apply_choices(s,'1',list(name=list(choice='later')),editor)
 expect_equal(s$tests[['1']]$choices$name$previous$value,'Careful wording');expect_equal(s$tests[['1']]$proposed$name,'Test 1')
 expect_error(apply_choices(s,'1',list(conditions=list(choice='later')),editor),'no Epic')
})
test_that('comparison is independent of mismatch position', {
 for(position in c(1,3,5)) {
  s<-exported_fixture();d<-attr(s,'rows');d$name<-paste('New name',seq_len(5));d$name[[position]]<-'Different'
  s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
  for(i in seq_len(5)) {
   if(i==position) {expect_length(open_fields(s$tests[[as.character(i)]]),1);expect_false(ready(s$tests[[as.character(i)]]))}
   else {expect_length(open_fields(s$tests[[as.character(i)]]),0);expect_true(confirmed_row(s$exports[[1]],as.character(i)))}
  };expect_length(s$exports[[1]]$retired,0)
 }
})
test_that('unchanged OLSD values still mismatch exported values', {
 s<-exported_fixture(1);d<-attr(s,'rows');s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
 expect_length(open_fields(s$tests[['1']]),1);expect_length(s$exports[[1]]$mismatches,1)
})
test_that('confirmed history survives edits and unconfirmed files retire', {
 s<-exported_fixture(2);d<-attr(s,'rows');d$name<-paste('New name',1:2)
 s<-apply_olsd(s,d,source_reference('OLSD',d),admin);receipt<-s$exports[[1]]$confirmed[['1']]
 s<-apply_choices(s,'1',list(conditions=list(choice='custom',value='Later conditions')),editor)
 expect_identical(s$exports[[1]]$confirmed[['1']],receipt);expect_length(s$exports[[1]]$retired,0)
 s<-exported_fixture(2);s<-send_back(s,'1',editor)
 expect_length(s$exports[[1]]$retired,1);expect_equal(status(s,s$tests[['2']]),'To download')
 d<-attr(s,'rows');d$name<-paste('New name',1:2);s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
 expect_false(confirmed_row(s$exports[[1]],'1'));expect_length(s$exports[[1]]$retired,1)
})
test_that('blocked maps prevent approval and ambiguous identities fail', {
 s<-fixture(1);e<-attr(s,'epic');e$sections<-'MISSING';s<-apply_epic(s,e,source_reference('Epic',e),admin)
 expect_error(apply_choices(s,'1',list(labs=list(choice='epic')),editor),'unavailable')
 expect_error(approve_tests(s,'1',editor));expect_error(validate_epic(rbind(e,e)),'unique')
})
test_that('prepared files cannot download changed approvals', {
 s<-approve_tests(accept_names(fixture(1)),'1',editor);x<-prepare_export(s,'1')[[1]]
 s<-apply_choices(s,'1',list(name=list(choice='custom',value='New wording')),editor)
 expect_error(record_download(s,x,editor,list()),'Approval changed')
})
test_that('later matching comparison resolves only the prior comparison mismatch', {
 s<-exported_fixture(2);d<-attr(s,'rows');d$name<-c('Different','New name 2');s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
 d$name<-c('New name 1','New name 2');s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
 expect_length(open_fields(s$tests[['1']]),0);expect_true(ready(s$tests[['1']]));expect_equal(status(s,s$tests[['1']]),'Confirmed in OLSD')
})
test_that('partial source updates retain per-test observation dates', {
 s<-fixture(2);earlier<-s$tests[['2']]$sources$olsd;d<-attr(s,'rows')[1,,drop=FALSE]
 ref<-source_reference('OLSD',d);ref$at<-'2026-11-04T12:00:00Z';s<-apply_olsd(s,d,ref,admin)
 expect_identical(s$tests[['2']]$sources$olsd,earlier);expect_identical(s$tests[['1']]$sources$olsd,ref)
})
test_that('resolving a mapping to the current OLSD value clears its blocker', {
 s<-fixture(1);s$mappings<-s$mappings[FALSE,];e<-attr(s,'epic');s<-apply_epic(s,e,source_reference('Epic',e),admin)
 expect_equal(s$tests[['1']]$blocked,'labs');s$mappings<-data.frame(section='CHEM',lab='Main lab',category='Chemistry')
 s<-apply_epic(s,e,source_reference('Epic',e),admin);expect_length(s$tests[['1']]$blocked,0);expect_false('labs'%in%open_fields(s$tests[['1']]))
})
test_that('vendor controls and test numbers are frozen with approval', {
 s<-exported_fixture(1);expect_equal(s$tests[['1']]$approval$number,'T1')
 d<-attr(s,'rows');d$name<-'New name 1';d$number<-'T1-CHANGED';d$managed_by<-'Vendor'
 s<-apply_olsd(s,d,source_reference('OLSD',d),admin)
 expect_equal(s$tests[['1']]$number,'T1-CHANGED');expect_false(ready(s$tests[['1']]))
 expect_false(confirmed_row(s$exports[[1]],'1'));expect_equal(s$exports[[1]]$rows[['1']]$number,'T1')
 expect_equal(s$exports[[1]]$rows[['1']]$vendor$managed_by,'Client')
})
