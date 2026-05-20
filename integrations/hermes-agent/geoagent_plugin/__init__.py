"""
Geoagent plugin for Hermes Agent.
Register tools to enable geoagent transformation capabilities.
"""

from .schemas import GEOAGENT_TRANSFORM_SCHEMA, GEOAGENT_BATCH_SCHEMA
from .tools import geoagent_transform_tool, geoagent_batch_tool


def register(ctx):
    """Register geoagent tools with Hermes Agent."""
    ctx.register_tool(
        name="geoagent_transform",
        toolset="geoagent",
        schema=GEOAGENT_TRANSFORM_SCHEMA,
        handler=geoagent_transform_tool
    )
    ctx.register_tool(
        name="geoagent_batch",
        toolset="geoagent",
        schema=GEOAGENT_BATCH_SCHEMA,
        handler=geoagent_batch_tool
    )