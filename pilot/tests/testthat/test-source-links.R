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
test_that('two procedures cannot claim the same OLSD entry', {
 expect_error(normalize_helix(raw_links(c('https://example.org/Tests/1','https://example.org/Tests/1'))),'OLSD IDs must be unique')
})
test_that('bare links and mixed-case paths are accepted without invented labels', {
 x<-normalize_helix(raw_links('https://example.org/site/tests/12; /Tests/13'))
 expect_equal(x$rows$id,c('12','13'));expect_equal(x$rows$link_label,c('',''))
})
