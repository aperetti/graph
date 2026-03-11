## 2025-03-08 - [SQL Injection in Map Voltage Use Case]
**Vulnerability:** SQL Injection via String Formatting in DuckDB Queries
**Learning:** `backend/src/analytics/map_voltage.py` was directly concatenating `start_time`, `end_time`, and list parameters into DuckDB SQL query strings, leading to potential SQL injection.
**Prevention:** Parameterize user inputs in SQL strings using standard DuckDB parameter binding `?`, dynamically constructing placeholders for SQL IN lists, and appropriately casting parameters (`CAST(? AS TIMESTAMP)`).
