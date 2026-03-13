## 2024-03-13 - [DuckDB Parameterized Array Queries]
**Vulnerability:** SQL Injection in DuckDB queries due to string interpolation for IN clauses and timestamps.
**Learning:** DuckDB with Python's DB-API requires dynamic generation of placeholders `?` matched to the exact length of the list, rather than injecting a formatted string. Timestamps also require explicit CAST(? AS TIMESTAMP) to prevent DuckDB parameter type inference errors from failing the query.
**Prevention:** Use `placeholders = ",".join(["?"] * len(nodes_to_query))` and append list variables followed by timestamp strings to the execution `params` array. Never use f-strings for DuckDB Python query parameters.
