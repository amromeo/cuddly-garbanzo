# Optional institutional adapter, excluded from the default deployment bundle.
read_helix_sql <- function() {
 sql<-file.path('sql','warehouse_catalog.sql')
 if(!file.exists(sql)) fail('Add your warehouse query at sql/warehouse_catalog.sql (relative to the pilot project root).')
 if(!requireNamespace('rocqi',quietly=TRUE)) fail('The approved institutional rocqi package is required.')
 conn<-rocqi::helix_prod()
 tryCatch(rocqi::run_sql_file(sql,conn=conn,lowercase_names=FALSE),finally=DBI::dbDisconnect(conn))
}
