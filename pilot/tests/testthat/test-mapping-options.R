test_that('mapping options use distinct source sections and observed OLSD names', {
 s<-fixture(2);s$tests[['1']]$olsd$labs<-'Main lab\nOutside lab';s$tests[['2']]$olsd$categories<-'Chemistry;Special list'
 x<-mapping_options(s,data.frame(sections=c('CHEM;NEW SECTION','CHEM')))
 expect_equal(x$sections,c('CHEM','NEW SECTION'));expect_equal(x$labs,c('Main lab','Outside lab'))
 expect_equal(x$categories,c('Chemistry','Special list'))
 expect_equal(nrow(s$mappings),1);expect_false('NEW SECTION'%in%s$mappings$section)
})
test_that('large catalog index preserves one status per test', {
 s<-fixture(1542);x<-worklist_index(s)
 expect_length(x$statuses,1542);expect_equal(as.integer(x$counts['To review']),1542)
 expect_equal(x$names,1542);expect_equal(x$blocked,0)
})
