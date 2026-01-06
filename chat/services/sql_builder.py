# chat/services/sql_builder.py
import os
import yaml


def load_metadata():
    metadata_path = os.path.join(os.getcwd(), "schema_metadata.yaml")
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)


def build_sql(plan: dict) -> tuple[str, list]:
    if "error" in plan:
        return "", []

    metadata = load_metadata()

    base_table = plan["table"]
    base_alias = plan["alias"]

    # Auto-fallback for COUNT intent
    if plan.get("intent") == "count":
        plan["columns"] = []
        plan["aggregations"] = [{
            "function": "COUNT",
            "column": f"{base_alias}.id",
            "alias": "total_count"
        }]
        plan["limit"] = 1


    def real_table(t):
        return f"chat_{t}"

    # FROM clause
    sql = f"SELECT "
    params = []
    # SELECT clause
    select_items = []


# 🚨 IMPORTANT RULE:
# If aggregations exist, DO NOT select normal columns (like e.*)
    if plan.get("aggregations"):
        pass  # only aggregations will be added
    else:
        if plan.get("columns") == ["*"]:
            select_items.append(f"{base_alias}.*")
        else:
            for col in plan.get("columns", []):
                alias, column = col.split(".", 1)
                select_items.append(
                    f"{alias}.{column} AS {alias}_{column}"
                )


    for agg in plan.get("aggregations", []):
        func = agg["function"]
        alias, column = agg["column"].split(".", 1)
        agg_alias = agg.get("alias", f"{func.lower()}_{alias}_{column}")
        select_items.append(
            f"{func}({alias}.{column}) AS {agg_alias}"
        )

    sql += ", ".join(select_items)

    sql += f" FROM {real_table(base_table)} AS {base_alias}"

    # JOINs
    for j in plan.get("joins", []):
        j_table = j["table"]
        j_alias = j["alias"]
        left, right = j["on"]

        sql += (
            f" INNER JOIN {real_table(j_table)} AS {j_alias}"
            f" ON {left} = {right}"
        )

    # WHERE
    where_clauses = []
    for f in plan.get("filters", []):
        col = f["column"]
        op = f["operator"]
        value = f.get("value")

        if value is None:
            where_clauses.append(f"{col} IS NULL")
        else:
            where_clauses.append(f"{col} {op} %s")
            params.append(value)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # GROUP BY
    if plan.get("group_by"):
        sql += " GROUP BY " + ", ".join(plan["group_by"])

    # ORDER BY
    if plan.get("order_by"):
        orders = [
            f"{o['column']} {o['direction']}"
            for o in plan["order_by"]
        ]
        sql += " ORDER BY " + ", ".join(orders)

    # LIMIT
    sql += f" LIMIT {plan.get('limit', 50)}"

    return sql, params
