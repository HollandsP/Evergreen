"""
API routes module
"""
from . import auth
from . import generation
from . import health
from . import projects
from . import scripts

__all__ = ["auth", "generation", "health", "projects", "scripts"]