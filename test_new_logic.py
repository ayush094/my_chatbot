import os
import sys
import json

# Add the project root to sys.path
sys.path.append(os.getcwd())

from chat.services.json_validator import validate_json
from chat.services.sql_builder import build_sql

def run_test(name, plan):
    print(f"\n--- Test: {name} ---")
    try:
        valid = validate_json(plan)
        print(f"Valid: {valid}")
        if valid:
            if "error" in plan:
                print("Plan contains error message as expected.")
                return
            sql, params = build_sql(plan)
            print(f"SQL: {sql}")
            print(f"Params: {params}")
    except Exception as e:
        print(f"Error running test: {e}")

# Test Case 1: Simple Select with Join
run_test("Simple Select with Join", {
  "table": "employee",
  "columns": ["employee.first_name", "department.name"],
  "joins": [
    {
      "table": "department",
      "on": "employee.department_id = department.id"
    }
  ],
  "limit": 10
})

# Test Case 2: Aggregation and Group By
run_test("Aggregation and Group By", {
  "table": "salary",
  "columns": ["employee.department_id"],
  "joins": [
    {
      "table": "employee",
      "on": "salary.employee_id = employee.id"
    }
  ],
  "aggregations": [
    {
      "function": "AVG",
      "column": "salary.amount",
      "alias": "avg_salary"
    }
  ],
  "group_by": ["employee.department_id"],
  "limit": 50
})

# Test Case 3: Order By and Filters
run_test("Order By and Filters", {
  "table": "attendance",
  "columns": ["*"],
  "filters": [
    {
      "column": "attendance.status",
      "operator": "=",
      "value": "Absent"
    },
    {
      "column": "attendance.date",
      "operator": ">=",
      "value": "2026-01-01"
    }
  ],
  "order_by": [
    {
      "column": "attendance.date",
      "direction": "DESC"
    }
  ],
  "limit": 20
})

# Test Case 4: Error handling
run_test("Query Not Possible", {
  "error": "Query not possible with available schema"
})

# Test Case 5: Invalid Table (should fail validation)
run_test("Invalid Table", {
  "table": "non_existent_table",
  "columns": ["*"]
})
