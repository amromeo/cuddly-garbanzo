# Optional institutional adapter, excluded from the default deployment bundle.
read_helix_sql <- function() {
 sql<-Sys.getenv('OLSD_HELIX_SQL')
 if(!nzchar(sql)||!file.exists(sql)) fail('Configure the institution-provided OLSD_HELIX_SQL file.')
 if(!requireNamespace('rocqi',quietly=TRUE)) fail('The approved institutional rocqi package is required.')
 conn<-rocqi::helix_prod()
 tryCatch(rocqi::run_sql_file(sql,conn=conn,lowercase_names=FALSE),finally=DBI::dbDisconnect(conn))
}
