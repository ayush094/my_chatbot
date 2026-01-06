# chat/services/json_validator.py
import os
import yaml


def load_metadata():
    metadata_path = os.path.join(os.getcwd(), "schema_metadata.yaml")
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)


def validate_json(plan: dict) -> bool:
    if not isinstance(plan, dict):
        return False

    # AI explicitly says query not possible
    if "error" in plan:
        return True

    metadata = load_metadata()
    tables_meta = metadata.get("tables", {})

    # Base table + alias
    base_table = plan.get("table")
    base_alias = plan.get("alias")

    if not base_table or base_table not in tables_meta:
        return False

    if not tables_meta[base_table].get("queryable", True):
        return False

    if not base_alias or not isinstance(base_alias, str):
        return False

    # Collect aliases → tables
    alias_map = {base_alias: base_table}

    joins = plan.get("joins", [])
    if not isinstance(joins, list):
        return False

    for join in joins:
        j_table = join.get("table")
        j_alias = join.get("alias")
        on = join.get("on")

        if not j_table or not j_alias or not on:
            return False

        if j_table not in tables_meta:
            return False

        if not tables_meta[j_table].get("queryable", True):
            return False

        # Self-join must use alias
        if j_table == base_table and j_alias == base_alias:
            return False

        if j_alias in alias_map:
            return False  # duplicate alias

        if not isinstance(on, list) or len(on) != 2:
            return False

        alias_map[j_alias] = j_table

    # Column validation helper
    def is_valid_column(col: str) -> bool:
        if col == "*":
            return True

        if "." not in col:
            return False  # aliases are mandatory

        alias, column = col.split(".", 1)
        table = alias_map.get(alias)

        if not table:
            return False

        return column in tables_meta[table].get("columns", {})

    # Columns
    columns = plan.get("columns", [])
    if not isinstance(columns, list):
        return False

    for col in columns:
        if not is_valid_column(col):
            return False

    # Filters
    allowed_ops = metadata.get("global_rules", {}).get(
        "allowed_operators", ["=", ">", "<", ">=", "<="]
    )

    for f in plan.get("filters", []):
        if not is_valid_column(f.get("column")):
            return False
        if f.get("operator") not in allowed_ops:
            return False

    # Aggregations
    allowed_aggs = metadata.get("global_rules", {}).get(
        "allowed_aggregations", ["COUNT", "SUM", "AVG", "MIN", "MAX"]
    )

    for agg in plan.get("aggregations", []):
        if agg.get("function") not in allowed_aggs:
            return False
        if not is_valid_column(agg.get("column")):
            return False

    # GROUP BY
    for g in plan.get("group_by", []):
        if not is_valid_column(g):
            return False

    # ORDER BY
    for o in plan.get("order_by", []):
        if not is_valid_column(o.get("column")):
            return False
        if o.get("direction") not in ["ASC", "DESC"]:
            return False

    # LIMIT
    limit = plan.get("limit", 50)
    if not isinstance(limit, int) or limit <= 0:
        return False

    return True
