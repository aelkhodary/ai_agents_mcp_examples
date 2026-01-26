# Chapter 6: Advanced Server Features

This chapter covers advanced MCP server capabilities including completions, context objects, notifications, elicitations, sampling, and more.

## Running Examples

```bash
uv run ch6/<example_folder>/server.py
```

## Examples Overview

### 01. Completions (`01_completions/`)

Implementing auto-completion suggestions for tool arguments.

```bash
uv run ch6/01_completions/server.py
```

**Files:**
- `server.py` - Server with completions
- `1.txt`, `2.png` - Sample files for completion

---

### 02. Server Icons (`02_server_icons/`)

Adding visual branding to your MCP server.

```bash
uv run ch6/02_server_icons/server.py
```

**Files:**
- `server.py` - Server configuration
- `brain.png`, `sloth.png` - Icon assets

---

### 03. Context Object - Server Info (`03_context_object_server_info/`)

Accessing server information from within tools.

**Key Concepts:**
- `Context` object usage
- Server metadata access

---

### 04. Context Object - Session Info (`04_context_object_session_info/`)

Accessing session information from within tools.

**Files:**
- `server.py` - Server implementation
- `knowledge.txt` - Sample data

**Key Concepts:**
- Session state
- Client capabilities

---

### 05. Context Object - Request Info (`05_context_object_request_info/`)

Accessing request-specific information.

**Key Concepts:**
- Request metadata
- Progress tokens

---

### 06. Context Object - Logging (`06_context_object_logging/`)

Server-side logging through the context object.

```bash
uv run ch6/06_context_object_logging/server.py
```

**Key Concepts:**
- `ctx.debug()`, `ctx.info()`, `ctx.warning()`, `ctx.error()`
- Log messages sent to client

**Implementation:**
```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP("context-object-logging-server")

@mcp.tool()
async def add(a: float, b: float, ctx: Context[ServerSession, None]) -> dict[str, float]:
    """Add two numbers together."""
    await ctx.info(f"{datetime.now()}: add called")
    try:
        result = {"augend": a, "addend": b, "sum": a + b}
    except Exception as e:
        await ctx.error(f"{datetime.now()}: error: {e}")
        raise e
    await ctx.debug(f"{datetime.now()}: add result: {result}")
    if result["sum"] < 0:
        await ctx.warning(f"{datetime.now()}: result is negative")
    return result
```

---

### 07. Progress Notification (FastMCP) (`07_progress_notification_fastmcp/`)

Sending progress updates during long-running operations.

**Key Concepts:**
- Progress notifications
- Percentage completion
- Status messages

---

### 08. Manual Notifications (`08_manual_notifications/`)

Sending custom notifications to the client.

---

### 10. Cancel Request Notification (`10_cancel_request_notification/`)

Handling request cancellation from the client.

**Key Concepts:**
- Cancellation tokens
- Graceful operation termination

---

### 11. Low-Level Pagination (`11_low_level_pagination/`)

Implementing pagination for large result sets.

**Key Concepts:**
- Cursor-based pagination
- Large data handling

---

### 12. Pings (`12_pings/`)

Keep-alive and health check mechanisms.

**Key Concepts:**
- Ping/pong protocol
- Connection health monitoring

---

### 13. Elicitations Server (`13_elicitations_server/`)

Server-initiated user input collection.

```bash
uv run ch6/13_elicitations_server/server.py
```

**Key Concepts:**
- `ctx.session.elicit()` API
- JSON Schema for form definition
- Handling accept/decline/cancel actions

**Implementation:**
```python
FORM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "title": "Full Name", "minLength": 1},
        "email": {"type": "string", "title": "Email", "format": "email"},
        "age": {"type": "number", "title": "Age", "minimum": 0, "maximum": 150},
    },
    "required": ["name", "email"],
}

@mcp.tool()
async def signup_math_facts(ctx: Context[ServerSession, None]) -> str:
    """Sign up to receive daily math facts."""
    elicit_result = await ctx.session.elicit(
        message="Please provide your information!",
        requestedSchema=FORM_SCHEMA,
    )
    
    if elicit_result.action == "accept":
        user_data = elicit_result.content
        return f"Welcome {user_data['name']}!"
    elif elicit_result.action == "decline":
        return "No problem!"
    else:  # cancel
        return "Signup cancelled."
```

---

### 14. Sampling (`14_sampling/`)

Server-initiated LLM requests.

```bash
uv run ch6/14_sampling/server.py
```

**Key Concepts:**
- `ctx.session.create_message()` API
- `ModelPreferences` and `ModelHint`
- Server calling LLM through client

**Implementation:**
```python
from mcp.types import ModelHint, ModelPreferences, SamplingMessage, TextContent

MODEL_PREFERENCES = ModelPreferences(
    hints=[
        ModelHint(name="claude-4-5-haiku"),
        ModelHint(name="gpt-4o-mini"),
    ],
    costPriority=1.0,
    speedPriority=0.8,
    intelligencePriority=0.3,
)

@mcp.tool()
async def explain_math(operation: str, ctx: Context[ServerSession, None]) -> str:
    """Use sampling to explain how a mathematical operation works."""
    
    # Check if client supports sampling
    if not ctx.session.client_params.capabilities.sampling:
        return "Sampling is not supported by this client"
    
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        max_tokens=100,
        model_preferences=MODEL_PREFERENCES,
    )
    
    return result.content.text
```

---

### 15. Roots (`15_roots/`)

Accessing client-provided file system roots.

**Key Concepts:**
- `ctx.session.list_roots()` API
- File path validation
- Sandboxed file access

---

### 16. Cancel Request Notification (`16_cancel_request_notification/`)

Additional cancellation handling patterns.

---

## Context Object Reference

The `Context` object provides access to server, session, and request information:

```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

@mcp.tool()
async def my_tool(arg: str, ctx: Context[ServerSession, None]) -> str:
    # Logging
    await ctx.debug("Debug message")
    await ctx.info("Info message")
    await ctx.warning("Warning message")
    await ctx.error("Error message")
    
    # Session access
    session = ctx.session
    
    # Check client capabilities
    if session.client_params.capabilities.sampling:
        # Client supports sampling
        pass
    
    # Request roots from client
    roots_result = await session.list_roots()
    
    # Request user input (elicitation)
    elicit_result = await session.elicit(message="...", requestedSchema={...})
    
    # Request LLM completion (sampling)
    message_result = await session.create_message(messages=[...], max_tokens=100)
    
    return "result"
```

---

## Server-to-Client Capabilities

| Capability | Method | Description |
|------------|--------|-------------|
| Logging | `ctx.info()`, etc. | Send log messages |
| Progress | Progress notifications | Report operation progress |
| Elicitation | `session.elicit()` | Request user input |
| Sampling | `session.create_message()` | Request LLM completion |
| Roots | `session.list_roots()` | Get file system boundaries |

---

## Model Preferences

When using sampling, specify model preferences:

```python
ModelPreferences(
    hints=[                           # Preferred models (in order)
        ModelHint(name="claude-4-5-haiku"),
        ModelHint(name="gpt-4o-mini"),
    ],
    costPriority=1.0,                # 0.0-1.0, higher = prefer cheaper
    speedPriority=0.8,               # 0.0-1.0, higher = prefer faster
    intelligencePriority=0.3,        # 0.0-1.0, higher = prefer smarter
)
```

---

## Elicitation Schema

Elicitation uses JSON Schema for form definition:

```python
{
    "type": "object",
    "properties": {
        "field_name": {
            "type": "string",          # string, number, integer, boolean
            "title": "Display Title",
            "description": "Help text",
            "minLength": 1,            # Validation
            "format": "email",         # Special formats
        },
    },
    "required": ["field_name"],        # Required fields
}
```

---

## Best Practices

1. **Logging** - Use appropriate log levels for debugging
2. **Progress** - Report progress for operations > 1 second
3. **Elicitation** - Provide clear messages and reasonable defaults
4. **Sampling** - Check client capability before using
5. **Roots** - Always validate paths against provided roots
6. **Error Handling** - Use context logging for errors
