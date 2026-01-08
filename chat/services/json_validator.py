# chat/services/json_validator.py

import os
import yaml
from django.conf import settings

# Column alias normalization for natural language
COLUMN_ALIAS_MAP = {
    "employee": {
        "name": ["first_name", "last_name"]
    }
}

def load_metadata():
    metadata_path = os.path.join(settings.BASE_DIR, "schema_metadata.yaml")
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)

def normalize_column_refs(columns, alias_map, tables):
    """
    Expands natural-language columns like employee.name
    into employee.first_name, employee.last_name
    """
    normalized = []

    for col_ref in columns:
        if col_ref == "*":
            normalized.append(col_ref)
            continue

        if "." not in col_ref:
            normalized.append(col_ref)
            continue

        alias, col_name = col_ref.split(".", 1)
        table = alias_map.get(alias)

        if table and col_name in COLUMN_ALIAS_MAP.get(table, {}):
            for real_col in COLUMN_ALIAS_MAP[table][col_name]:
                normalized.append(f"{alias}.{real_col}")
        else:
            normalized.append(col_ref)

    return normalized



def validate_json(plan: dict) -> bool:
    """
    Validates the AI-generated JSON plan against schema_metadata.yaml
    """
    import logging
    logger = logging.getLogger(__name__)

    if "error" in plan:
        return True

    try:
        metadata = load_metadata()
        tables = metadata.get("tables", {})
        action = plan.get("action", "query")

        # 0. Bypass validation for specialty ORM actions handled in views
        if action == "approve_leave":
            return True

        # 1. Action-specific validation
        if action in ["insert", "update"]:

            table_name = plan.get("table")
            if table_name != "leave":
                logger.warning(f"Validation failed: Unauthorized {action} on table '{table_name}'. Only 'leave' is permitted.")
                return False
            
            if action == "update" and not plan.get("filters"):
                logger.warning("Validation failed: UPDATE statement missing WHERE clause (filters).")
                return False

        # 2. Map Aliases to Tables
        base_table_name = plan.get("table")
        base_alias = plan.get("alias") or base_table_name
        
        if not base_table_name or base_table_name not in tables:
            logger.warning(f"Validation failed: Base table '{base_table_name}' not in metadata.")
            return False

        if action == "query" and not tables[base_table_name].get("queryable", True):
            logger.warning(f"Validation failed: Table '{base_table_name}' is not queryable.")
            return False

        alias_map = {base_alias: base_table_name}
        
        for join in plan.get("joins", []):
            j_table = join.get("table")
            j_alias = join.get("alias") or j_table
            if j_table not in tables:
                logger.warning(f"Validation failed: Joined table '{j_table}' not in metadata.")
                return False
            alias_map[j_alias] = j_table

        # 3. Validate Columns / data
        if action == "query":
            columns = plan.get("columns", [])

            # 🔥 NORMALIZE ALIASES (THIS FIXES 'name')
            columns = normalize_column_refs(columns, alias_map, tables)
            plan["columns"] = columns

            
            for col_ref in columns:
                if col_ref == "*":
                    continue
                
                if "." not in col_ref:
                    logger.warning(f"Validation failed: Column '{col_ref}' must be alias-qualified.")
                    return False
                    
                alias, col_name = col_ref.split(".", 1)
                if alias not in alias_map:
                    logger.warning(f"Validation failed: Alias '{alias}' not defined in plan.")
                    return False
                
                actual_table = alias_map[alias]
                if col_name not in tables[actual_table].get("columns", {}):
                    logger.warning(f"Validation failed: Column '{col_name}' not in table '{actual_table}'.")
                    return False
        else: # INSERT or UPDATE
            data = plan.get("data", {})
            if not data:
                logger.warning(f"Validation failed: {action} action missing 'data'.")
                return False
            
            for col_name in data.keys():
                if col_name not in tables[base_table_name].get("columns", {}):
                    logger.warning(f"Validation failed: Column '{col_name}' not in table '{base_table_name}'.")
                    return False

        # 4. Validate Filters
        for f in plan.get("filters", []):
            col_ref = f.get("column")
            if not col_ref:
                return False
            
            if "." in col_ref:
                alias, col_name = col_ref.split(".", 1)
                
                # For mutations, if the alias is not define, we try just the col_name on base_table
                if action == "query" or alias in alias_map:
                    if alias not in alias_map:
                        logger.warning(f"Validation failed: Filter alias '{alias}' not defined.")
                        return False
                    actual_table = alias_map[alias]
                else:
                    # For INSERT/UPDATE, we can be more lenient and ignore the alias if it matches base_table context
                    col_name = col_name # strip alias
                    actual_table = base_table_name
            else:
                col_name = col_ref
                actual_table = base_table_name
            
            if col_name not in tables[actual_table].get("columns", {}):
                logger.warning(f"Validation failed: Filter column '{col_name}' not in table '{actual_table}'.")
                return False

        return True


    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False



