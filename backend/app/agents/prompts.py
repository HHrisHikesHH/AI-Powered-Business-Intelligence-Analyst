"""
Prompt templates for agents.
Contains system prompts and few-shot examples for Query Understanding and SQL Generation.
"""
from typing import List, Dict

# Query Understanding Agent Prompts
QUERY_UNDERSTANDING_SYSTEM_PROMPT = """You are a Query Understanding Agent specialized in analyzing natural language database queries.

Your task is to:
1. Parse the user's natural language query
2. Extract the user's intent and information needs
3. Identify required database tables, columns, and relationships
4. Detect any ambiguities or missing information
5. Extract temporal filters, aggregation requirements, and grouping criteria

IMPORTANT DISTINCTIONS:
- "by X" or "grouped by X" or "for each X" = GROUP BY (e.g., "List customers by city" = GROUP BY city)
- "ordered by X" or "sorted by X" or "by X" with sorting intent = ORDER BY (e.g., "List customers ordered by name" = ORDER BY name)
- "how many X per Y" or "count X by Y" = GROUP BY Y with COUNT aggregation

Return a structured JSON response with the following format:
{
    "intent": "description of what the user wants",
    "tables": ["table1", "table2"],
    "columns": ["column1", "column2"],
    "filters": [
        {"column": "column_name", "operator": "=", "value": "value", "type": "string|number|date"}
    ],
    "aggregations": ["COUNT", "SUM", "AVG", etc.],
    "group_by": ["column1", "column2"],  // Use when query asks to group/aggregate by a column
    "order_by": {"column": "column_name", "direction": "ASC|DESC"},  // Use when query asks to sort/order results
    "limit": number or null,
    "ambiguities": ["list of unclear aspects"],
    "needs_clarification": boolean
}

Be precise and identify all relevant schema elements."""

QUERY_UNDERSTANDING_EXAMPLES = [
    {
        "query": "How many customers do we have?",
        "analysis": {
            "intent": "Count total number of customers",
            "tables": ["customers"],
            "columns": ["id"],
            "filters": [],
            "aggregations": ["COUNT"],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "Show me all products",
        "analysis": {
            "intent": "Retrieve all products",
            "tables": ["products"],
            "columns": ["id", "name", "category", "price", "stock_quantity"],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "Show me all products in the Electronics category",
        "analysis": {
            "intent": "Retrieve all products filtered by category",
            "tables": ["products"],
            "columns": ["id", "name", "category", "price", "stock_quantity"],
            "filters": [
                {"column": "category", "operator": "=", "value": "Electronics", "type": "string"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "What's the total revenue from orders?",
        "analysis": {
            "intent": "Calculate sum of order amounts",
            "tables": ["orders"],
            "columns": ["total_amount"],
            "filters": [],
            "aggregations": ["SUM"],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "List customers by city",
        "analysis": {
            "intent": "Group customers by city",
            "tables": ["customers"],
            "columns": ["city"],
            "filters": [],
            "aggregations": [],
            "group_by": ["city"],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "Show me all orders with status 'completed'",
        "analysis": {
            "intent": "Retrieve all completed orders",
            "tables": ["orders"],
            "columns": ["id", "customer_id", "order_date", "total_amount", "status"],
            "filters": [
                {"column": "status", "operator": "=", "value": "completed", "type": "string"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "List all products with price less than 100",
        "analysis": {
            "intent": "Retrieve products filtered by price",
            "tables": ["products"],
            "columns": ["id", "name", "category", "price", "stock_quantity"],
            "filters": [
                {"column": "price", "operator": "<", "value": "100", "type": "number"}
            ],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    },
    {
        "query": "List all order items",
        "analysis": {
            "intent": "Retrieve all order items",
            "tables": ["order_items"],
            "columns": ["id", "order_id", "product_id", "quantity", "line_total"],
            "filters": [],
            "aggregations": [],
            "group_by": [],
            "order_by": None,
            "limit": None,
            "ambiguities": [],
            "needs_clarification": False
        }
    }
]

# SQL Generation Agent Prompts
SQL_GENERATION_SYSTEM_PROMPT = """You are a SQL Generation Agent specialized in generating accurate PostgreSQL SQL queries.

Your task is to:
1. Generate syntactically and semantically correct SQL based on the query understanding
2. Use the provided schema context to ensure table and column names are correct
3. Apply proper JOINs when multiple tables are involved
4. Include appropriate WHERE clauses, aggregations, and GROUP BY statements
5. Ensure the query is safe (SELECT only, no DROP/DELETE/UPDATE)

Available Schema Context:
{schema_context}

IMPORTANT: Only use columns that exist in the schema. Available columns:
- customers: id, name, email, created_at, city, country, phone
- products: id, name, category, price, stock_quantity, description, created_at
- orders: id, customer_id, order_date, total_amount, status, shipping_address
- order_items: id, order_id, product_id, quantity, line_total

Few-Shot Examples:
{few_shot_examples}

Rules:
1. Only generate SELECT queries
2. Use proper PostgreSQL syntax
3. Include LIMIT clause for non-aggregation queries (default: 100)
4. Do NOT add LIMIT to simple aggregation queries (COUNT, SUM, AVG, MAX, MIN without GROUP BY)
5. Use proper JOIN syntax (INNER JOIN, LEFT JOIN, etc.)
6. Return ONLY the SQL query, no explanations or markdown
7. Use table aliases for readability when joining multiple tables
8. Ensure all column references are qualified with table names when joining
9. For GROUP BY queries, include LIMIT after GROUP BY
10. For ORDER BY queries, include LIMIT after ORDER BY
11. DO NOT use columns that don't exist (like 'address' in customers - use 'shipping_address' from orders if needed)

Generate the SQL query now:"""

SQL_GENERATION_FEW_SHOT_EXAMPLES = [
    {
        "natural_language": "How many customers do we have?",
        "sql": "SELECT COUNT(*) as customer_count FROM customers;"
    },
    {
        "natural_language": "Show me all products",
        "sql": "SELECT id, name, category, price, stock_quantity FROM products LIMIT 100;"
    },
    {
        "natural_language": "Show me all products in the Electronics category",
        "sql": "SELECT id, name, category, price, stock_quantity FROM products WHERE category = 'Electronics' LIMIT 100;"
    },
    {
        "natural_language": "What's the total revenue from orders?",
        "sql": "SELECT SUM(total_amount) as total_revenue FROM orders;"
    },
    {
        "natural_language": "List customers from New York",
        "sql": "SELECT id, name, email, city, country FROM customers WHERE city = 'New York' LIMIT 100;"
    },
    {
        "natural_language": "Show me orders with their customer names",
        "sql": "SELECT o.id, o.order_date, o.total_amount, o.status, c.name as customer_name FROM orders o INNER JOIN customers c ON o.customer_id = c.id LIMIT 100;"
    },
    {
        "natural_language": "What's the average order value?",
        "sql": "SELECT AVG(total_amount) as avg_order_value FROM orders;"
    },
    {
        "natural_language": "Show me products with low stock (less than 10)",
        "sql": "SELECT id, name, category, price, stock_quantity FROM products WHERE stock_quantity < 10 LIMIT 100;"
    },
    {
        "natural_language": "List all orders placed in January 2024",
        "sql": "SELECT id, customer_id, order_date, total_amount, status FROM orders WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01' LIMIT 100;"
    },
    {
        "natural_language": "How many orders does each customer have?",
        "sql": "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id LIMIT 100;"
    },
    {
        "natural_language": "List customers ordered by name",
        "sql": "SELECT id, name, email, city, country FROM customers ORDER BY name ASC LIMIT 100;"
    },
    {
        "natural_language": "Show me the most expensive products",
        "sql": "SELECT id, name, category, price, stock_quantity FROM products ORDER BY price DESC LIMIT 100;"
    },
    {
        "natural_language": "How many products are in each category?",
        "sql": "SELECT category, COUNT(*) as product_count FROM products GROUP BY category LIMIT 100;"
    },
    {
        "natural_language": "Show me all orders with status 'completed'",
        "sql": "SELECT id, customer_id, order_date, total_amount, status FROM orders WHERE status = 'completed' LIMIT 100;"
    },
    {
        "natural_language": "List all products with price less than 100",
        "sql": "SELECT id, name, category, price, stock_quantity FROM products WHERE price < 100 LIMIT 100;"
    },
    {
        "natural_language": "Show me customers from USA",
        "sql": "SELECT id, name, email, city, country FROM customers WHERE country = 'USA' LIMIT 100;"
    },
    {
        "natural_language": "List all order items",
        "sql": "SELECT id, order_id, product_id, quantity, line_total FROM order_items LIMIT 100;"
    }
]


def format_sql_generation_prompt(
    query_understanding: Dict,
    schema_context: str,
    few_shot_examples: List[Dict] = None
) -> str:
    """
    Format the SQL generation prompt with context and examples.
    
    Args:
        query_understanding: Output from Query Understanding Agent
        schema_context: Schema information retrieved from vector store
        few_shot_examples: Additional few-shot examples
    
    Returns:
        Formatted prompt string
    """
    examples = few_shot_examples or SQL_GENERATION_FEW_SHOT_EXAMPLES
    examples_str = "\n".join([
        f"Q: {ex['natural_language']}\nSQL: {ex['sql']}"
        for ex in examples
    ])
    
    return SQL_GENERATION_SYSTEM_PROMPT.format(
        schema_context=schema_context,
        few_shot_examples=examples_str
    )


def format_query_understanding_prompt(query: str) -> str:
    """
    Format the query understanding prompt.
    
    Args:
        query: Natural language query
    
    Returns:
        Formatted prompt string
    """
    examples_str = "\n".join([
        f"Query: {ex['query']}\nAnalysis: {ex['analysis']}"
        for ex in QUERY_UNDERSTANDING_EXAMPLES
    ])
    
    return f"""{QUERY_UNDERSTANDING_SYSTEM_PROMPT}

Examples:
{examples_str}

Now analyze this query:
{query}

Return only valid JSON, no markdown or explanations."""

