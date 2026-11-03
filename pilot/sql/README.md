# Warehouse query

Add your institutional query here as `warehouse_catalog.sql`. The direct adapter reads `sql/warehouse_catalog.sql` relative to the pilot project root. Keep connection credentials in environment variables, outside the SQL file.

Return these exact column names (using SQL aliases if needed):

- `Procedure ID`
- `Test Menu Links`
- `Procedure Display Name`
- `Authorized Lab Sections`

The actual query is institution-specific and is intentionally not supplied here. The source-job deployment must include this file; the Shiny app does not need it.
