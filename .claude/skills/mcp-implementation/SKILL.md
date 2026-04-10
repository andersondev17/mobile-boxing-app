---
name: mcp-implementation
description: Apply this skill when implementing MCP (Model Context Protocol) tools for the boxing app, exposing FastAPI endpoints as MCP tools via fastmcp, or configuring MCP servers in .mcp.json. Trigger on: "MCP", "model context protocol", "fastmcp", "expose as MCP tool", "mcp server", "mcp tool", "@mcp.tool", "FastMCP.from_fastapi", "mcp.json".
---

# MCP Implementation — mobile-boxing-app

## Current .mcp.json (project root)
File: `boxing-api/.mcp.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "/c/Users/Federico/Documents/projects/boxing-api"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "mongodb": {
      "command": "npx",
      "args": ["-y", "@mongodb-js/mongodb-mcp-server"],
      "env": {"MDB_MCP_CONNECTION_STRING": "${MONGODB_URI}"}
    }
  }
}
```

## Verifying MCP connections
```bash
claude mcp list
```

## Exposing FastAPI as MCP server (Phase 2)

Use `fastmcp` to turn boxing backend endpoints into Claude-accessible tools:

```python
# apps/backend/app/mcp_server.py
from fastmcp import FastMCP
from main import app as fastapi_app

# Option 1: Wrap existing FastAPI app
mcp = FastMCP.from_fastapi(fastapi_app)

# Option 2: Define tools explicitly
mcp = FastMCP("boxing-backend")

@mcp.tool()
async def get_boxing_status() -> dict:
    """Get the current boxing service status including baseline and session stats."""
    return await boxing_service.get_status()

@mcp.tool()
async def list_recent_sessions(user_id: str, limit: int = 10) -> list:
    """List recent boxing sessions for a user.

    Args:
        user_id: The user's MongoDB ObjectId as string.
        limit: Maximum number of sessions to return (default 10).
    """
    sessions = await BoxingSession.find(
        BoxingSession.user_id == user_id
    ).sort("-created_at").limit(limit).to_list()
    return [s.dict() for s in sessions]

@mcp.tool()
async def check_consent(user_id: str, consent_type: str) -> bool:
    """Check if a user has granted a specific consent type.

    Args:
        user_id: The user's ID.
        consent_type: One of "biometric_data", "health_data", "personal_data".
    """
    consent = await Consent.find_one(
        Consent.user_id == user_id,
        Consent.consent_type == consent_type,
        Consent.granted == True
    )
    return consent is not None
```

## Recommended endpoints to expose as MCP tools
| Endpoint | MCP Tool Name | Why useful |
|----------|--------------|------------|
| `GET /boxing/status` | `get_boxing_status` | Check service health |
| `GET /boxing/sessions` | `list_sessions` | Query session history |
| `GET /exercises/` | `list_exercises` | Browse exercise catalog |
| `GET /consent/{user_id}/check` | `check_consent` | Verify consent before ops |
| `GET /kafka/smartwatch/messages` | `get_smartwatch_data` | Debug telemetry |

## Adding to .mcp.json (when backend MCP is ready)
```json
{
  "mcpServers": {
    "boxing-backend": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/c/Users/Federico/Documents/projects/boxing-api/apps/backend/app"
    }
  }
}
```
