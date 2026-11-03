library(testthat)
results<-test_dir('tests/testthat',reporter='summary',stop_on_failure=TRUE)
summary<-as.data.frame(results)
jsonlite::write_json(list(at=format(Sys.time(),'%Y-%m-%dT%H:%M:%SZ',tz='UTC'),tests=nrow(summary),passed=sum(summary$passed),failed=sum(summary$failed),errors=sum(summary$error)),Sys.getenv('OLSD_TEST_REPORT','/tmp/olsd-pilot-r-results.json'),auto_unbox=TRUE,pretty=TRUE)
