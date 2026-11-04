raw_links<-function(links,procedures=seq_along(links)) data.frame('Procedure ID'=procedures,'Test Menu Links'=links,'Procedure Display Name'=paste('Procedure',procedures),'Authorized Lab Sections'='CHEM',check.names=FALSE)
test_that('one procedure expands to multiple independently identified OLSD entries', {
 x<-normalize_helix(raw_links('Test Info-Blood: https://example.org/Site/Tests/1; Test Info-CSF: https://example.org/site/Tests/2'))
 expect_equal(x$rows$id,c('1','2'));expect_equal(x$rows$epic_id,c('1','1'))
 expect_equal(x$rows$link_label,c('Test Info-Blood','Test Info-CSF'));expect_equal(nrow(x$excluded),0)
 expect_silent(validate_epic(x$rows))
 s<-fixture(2);s$tests[['1']]$olsd$name<-'Blood-specific name';s$tests[['1']]$proposed$name<-'Blood-specific name'
 s<-apply_epic(s,x$rows,source_reference('Epic',x$rows),admin)
 expect_equal(s$tests[['1']]$proposed$name,'Blood-specific name');expect_equal(s$tests[['1']]$link_label,'Test Info-Blood')
 s<-apply_choices(s,'1',list(name=list(choice='olsd')),editor)
 expect_length(s$tests[['1']]$pending,0);expect_true('name'%in%open_fields(s$tests[['2']]))
})
test_that('repeated links deduplicate and unlinked procedures remain excluded', {
 x<-normalize_helix(raw_links(c('Blood: https://example.org/Tests/1; Blood: https://example.org/Tests/1','No link')))
 expect_equal(nrow(x$rows),1);expect_equal(x$rows$link_label,'Blood');expect_equal(nrow(x$excluded),1)
})
test_that('several procedures link to one OLSD entry without duplicate worklist records', {
 x<-normalize_helix(raw_links(c('https://example.org/Tests/1','https://example.org/Tests/1')))
 expect_equal(nrow(x$rows),2)
 s<-apply_epic(fixture(1),x$rows,source_reference('Epic',x$rows),admin)
 expect_length(s$tests,1);expect_equal(nrow(s$tests[['1']]$linked_procedures),2)
 expect_true(s$tests[['1']]$source_conflict);expect_false(can_approve(s$tests[['1']]))
 expect_equal(s$tests[['1']]$proposed$name,'Test 1')
 expect_error(assign_procedure(s,'1','1',x$rows,source_reference('Epic',x$rows),editor),'Administrator')
 s<-assign_procedure(s,'1','2',x$rows,source_reference('Epic',x$rows),admin)
 expect_false(s$tests[['1']]$source_conflict);expect_equal(s$tests[['1']]$epic$name,'Procedure 2')
 expect_equal(nrow(s$tests[['1']]$linked_procedures),2)
 removed<-x$rows[x$rows$epic_id=='1',,drop=FALSE]
 s<-apply_epic(s,removed,source_reference('Epic',removed),admin)
 expect_true(s$tests[['1']]$source_conflict)
})

test_that('identical shared sources need no arbitrary primary selection', {
 x<-raw_links(c('https://example.org/Tests/1','https://example.org/Tests/1'));x[['Procedure Display Name']]<-'Common name'
 rows<-normalize_helix(x)$rows;s<-apply_epic(fixture(1),rows,source_reference('Epic',rows),admin)
 expect_false(s$tests[['1']]$source_conflict);expect_equal(s$tests[['1']]$epic$name,'Common name')
 expect_error(validate_epic(rbind(rows,rows[1,,drop=FALSE])),'unique')
})
test_that('bare links and mixed-case paths are accepted without invented labels', {
 x<-normalize_helix(raw_links('https://example.org/site/tests/12; /Tests/13'))
 expect_equal(x$rows$id,c('12','13'));expect_equal(x$rows$link_label,c('',''))
})
test_that('an entry losing all source links returns to assignment review', {
 s<-fixture(2);rows<-attr(s,'epic');s<-apply_epic(s,rows,source_reference('Epic',rows),admin)
 rows<-rows[rows$id=='2',,drop=FALSE];s<-apply_epic(s,rows,source_reference('Epic',rows),admin)
 expect_true(s$tests[['1']]$source_conflict);expect_equal(nrow(s$tests[['1']]$linked_procedures),0)
 expect_false(s$tests[['2']]$source_conflict)
})
