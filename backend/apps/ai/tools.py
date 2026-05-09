"""
Claude tool definitions for CivicLens.
Each tool maps to a real backend action: search ES, aggregate stats, or set alert.
"""

TOOLS = [
    {
        "name": "search_incidents",
        "description": (
            "Search public incident reports using keywords and filters. "
            "Returns matching incidents with location data for map display."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Free-text search query"},
                "category": {
                    "type": "string",
                    "enum": ["noise", "crime", "transit", "sanitation", "infrastructure", "emergency", "other"],
                    "description": "Incident category filter",
                },
                "borough": {
                    "type": "string",
                    "enum": ["Manhattan", "Brooklyn", "Queens", "The Bronx", "Staten Island"],
                    "description": "NYC borough to filter by",
                },
                "days": {"type": "integer", "description": "Only return incidents from the last N days", "default": 30},
                "lat": {"type": "number", "description": "Center latitude for geo filter"},
                "lng": {"type": "number", "description": "Center longitude for geo filter"},
                "radius_km": {"type": "number", "description": "Radius in km for geo filter", "default": 5},
                "limit": {"type": "integer", "description": "Max results to return", "default": 50},
            },
            "required": [],
        },
    },
    {
        "name": "aggregate_stats",
        "description": "Get aggregate statistics: counts by category, borough, or time period. Use for trend questions like 'which neighborhoods have the most noise complaints this week'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": ["category", "borough", "source", "status", "day"],
                    "description": "Field to group and count by",
                },
                "category": {"type": "string", "description": "Optional category filter"},
                "borough": {"type": "string", "description": "Optional borough filter"},
                "days": {"type": "integer", "description": "Time window in days", "default": 7},
            },
            "required": ["group_by"],
        },
    },
    {
        "name": "filter_by_area",
        "description": "Get incidents within a named NYC neighborhood or borough boundary. More precise than a radius — use when user says 'near Prospect Park' or 'in Bushwick'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "area_name": {"type": "string", "description": "Neighborhood or landmark name (e.g. 'Bushwick', 'Central Park')"},
                "category": {"type": "string", "description": "Optional category filter"},
                "days": {"type": "integer", "default": 30},
            },
            "required": ["area_name"],
        },
    },
    {
        "name": "set_alert",
        "description": "Subscribe to real-time alerts for a query. When new incidents matching the criteria arrive, the user will be notified via WebSocket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query to monitor"},
                "category": {"type": "string"},
                "borough": {"type": "string"},
                "radius_km": {"type": "number", "default": 2},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
            },
            "required": ["query"],
        },
    },
]
