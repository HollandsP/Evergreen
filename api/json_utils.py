"""
JSON utilities for custom serialization
"""
import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi.responses import JSONResponse


# Custom JSON encoder for datetime and other objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


# Custom JSON response class
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            cls=CustomJSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")