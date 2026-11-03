# Uses an already registered rsconnect account. Credentials are never embedded.
args<-commandArgs(TRUE)
if(length(args)!=2||!args[[1]]%in%c('development','pilot')||!args[[2]]%in%c('app','source-job')) stop('Usage: Rscript scripts/deploy.R development|pilot app|source-job',call.=FALSE)
if(!requireNamespace('rsconnect',quietly=TRUE)) stop('Restore renv dependencies first.')
server<-Sys.getenv('OLSD_CONNECT_SERVER_NAME');account<-Sys.getenv('OLSD_CONNECT_ACCOUNT')
if(!nzchar(server)||!nzchar(account)) stop('Register your institutional rsconnect account, then set OLSD_CONNECT_SERVER_NAME and OLSD_CONNECT_ACCOUNT.')
files<-c('renv.lock',list.files('R',recursive=TRUE,full.names=TRUE))
if(args[[2]]=='app') files<-c(files,'app.R',list.files('www',recursive=TRUE,full.names=TRUE)) else files<-c(files,'source_job.R','jobs/refresh_epic.R')
if(args[[2]]=='source-job'&&identical(Sys.getenv('OLSD_INCLUDE_HELIX_ADAPTER'),'true')) {
 if(!requireNamespace('rocqi',quietly=TRUE)) stop('Install and lock the approved institutional rocqi version before including the direct adapter.')
 if(!file.exists('sql/warehouse_catalog.sql')) stop('Add sql/warehouse_catalog.sql before deploying the direct adapter.')
 files<-c(files,'jobs/helix_direct.R','sql/warehouse_catalog.sql')
}
rsconnect::deployApp(appDir='.',appFiles=files,appName=paste('olsd',args[[1]],args[[2]],sep='-'),account=account,server=server,
 appPrimaryDoc=if(args[[2]]=='app') 'app.R' else 'source_job.R',appMode=if(args[[2]]=='app') 'shiny' else 'r',launch.browser=FALSE)
cat('Deployment uploaded. Keep access restricted; configure variables and complete the runbook before enabling pilot writes.\n')
