tool_template = {
    "name": "tool_name",
    "description": "Plain English explanation of what this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "What this parameter is and what it accepts"
            }
        },
        "required": ["param_name"]
    }
}

tool_get_customer = {
    "name": "get_customer",
    "description": "obtain customer by customer ID. returns customer's full profile.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "customer ID, e.g. C-123"
            }
        },
        "required": ["id"]
    }
}

tool_lookup_order = {
    "name": "lookup_order",
    "description": "obtain order by order ID. returns full details of order.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "order ID, e.g. O-123"
            }
        },
        "required": ["id"]
    }
}

tools = [tool_get_customer, tool_lookup_order]
