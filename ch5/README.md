# Chapter 5: Building MCP Servers

This chapter teaches you how to build MCP servers that expose tools, resources, and prompts to client applications.

## Running Servers

MCP servers can be run in different modes:

```bash
# Run with stdio transport (for subprocess communication)
uv run ch5/05_minimal_stdio_server/server.py

# Run with HTTP transport
# (modify server.py to use mcp.run(transport="streamable-http"))
```

## Examples Overview

### 01. Start Low-Level Server (`01_start_low_level_server/`)

Basic server setup using the low-level MCP API.

```bash
uv run ch5/01_start_low_level_server/server.py
```

**Key Concepts:**
- `Server` class from `mcp.server.lowlevel`
- Manual initialization options
- Capability configuration

**Implementation:**
```python
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

server = Server("low-level-server")

async def run():
    initialization_options = InitializationOptions(
        server_name="low-level-server",
        server_version="0.1.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=initialization_options,
        )
```

---

### 02. Low-Level List/Call Tools (`02_low_level_list_call_tools/`)

Implementing tools with the low-level API.

**Key Concepts:**
- Tool registration with decorators
- Manual tool listing and calling

---

### 03. Low-Level Structured Output (`03_low_level_structured_output/`)

Returning structured data from tools.

---

### 04. Lifespan Management (`04_lifespan_management/`)

Managing server lifecycle and resources.

**Key Concepts:**
- Startup and shutdown hooks
- Resource initialization/cleanup

---

### 05. Minimal Stdio Server (`05_minimal_stdio_server/`)

The simplest possible MCP server using FastMCP.

```bash
uv run ch5/05_minimal_stdio_server/server.py
```

**Implementation:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("minimal-stdio-server")

if __name__ == "__main__":
    mcp.run()  # Defaults to stdio transport
```

---

### 06. Structured Output (`06_structured_output/`)

Tools that return structured Pydantic models.

**Key Concepts:**
- Pydantic model integration
- Automatic schema generation

---

### 07. Full Tool (`07_full_tool/`)

Complete tool implementation with all features.

```bash
uv run ch5/07_full_tool/server.py
```

**Key Concepts:**
- `@mcp.tool()` decorator with options
- `ToolAnnotations` for metadata
- Complex input/output types
- Optional `structured_output` flag

**Implementation:**
```python
from mcp.types import ToolAnnotations
from pydantic import BaseModel

class ReportCard(BaseModel):
    name: str
    grades: list[Class]
    weighted_gpa: float | None = None

@mcp.tool(
    title="Calculate GPA",
    annotations=ToolAnnotations(readOnlyHint=True),
    structured_output=False,
)
def grader_calculate_gpa(classes: list[Class], weighted: bool = True) -> float:
    """Calculate the GPA for a list of classes."""
    # Implementation
```

---

### 08. Simple Prompt (`08_simple_prompt/`)

Basic prompt implementation.

```bash
uv run ch5/08_simple_prompt/server.py
```

**Key Concepts:**
- `@mcp.prompt()` decorator
- Return string for simple prompts

---

### 09. Multi-turn Prompt (`09_multiturn_prompt/`)

Prompts with multiple conversation turns.

```bash
uv run ch5/09_multiturn_prompt/server.py
```

**Key Concepts:**
- `UserMessage` and `AssistantMessage`
- Returning message lists
- Assistant prefill technique

**Implementation:**
```python
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage

@mcp.prompt()
async def multiturn_prompt(
    main_idea_count: int, user_text: str
) -> list[UserMessage | AssistantMessage]:
    user_input = UserMessage(content=f"Create {main_idea_count} main ideas...")
    assistant_prefill = AssistantMessage(content=f"Here are {main_idea_count} main ideas:\n1.")
    return [user_input, assistant_prefill]
```

---

### 10. Tool-Use Prompt (`10_tool_use_prompt/`)

Prompts that guide tool usage.

---

### 11. Resource Prompt (`11_resource_prompt/`)

Prompts that reference resources.

**Files:**
- `server.py` - Server implementation
- `knowledge.txt` - Sample knowledge base

---

### 12. Basic Resource (`12_basic_resource/`)

Simple resource implementation.

```bash
uv run ch5/12_basic_resource/server.py
```

**Key Concepts:**
- `@mcp.resource()` decorator
- Resource URI format
- Reading file contents

**Implementation:**
```python
from pathlib import Path
from mcp import Resource

@mcp.resource("file://knowledge.txt")
async def knowledge_base() -> Resource:
    """A resource that loads a text-based knowledge base."""
    knowledge_path = Path(__file__).parent / "knowledge.txt"
    with open(knowledge_path, "r") as f:
        return f.read()
```

---

### 13. Resource Template (`13_resource_template/`)

Dynamic resources with URI templates.

**Files:**
- `server.py` - Server with template
- `1.txt`, `2.png` - Sample files

**Key Concepts:**
- URI templates with parameters
- Dynamic resource generation

---

### 14. Resource Objects (`14_resource_objects/`)

Resources returning structured objects.

**Key Concepts:**
- Blob resources for binary data
- MIME type handling

---

## FastMCP vs Low-Level API

| Feature | FastMCP | Low-Level |
|---------|---------|-----------|
| Ease of use | High | Low |
| Flexibility | Medium | High |
| Boilerplate | Minimal | Significant |
| Decorators | Yes | No |
| Auto-schema | Yes | Manual |

**Recommendation:** Use FastMCP for most use cases. Use low-level API when you need fine-grained control.

---

## Tool Decorator Options

```python
@mcp.tool(
    title="Human-readable title",           # Display name
    annotations=ToolAnnotations(            # Metadata hints
        readOnlyHint=True,                  # Tool doesn't modify state
        destructiveHint=False,              # Tool is not destructive
        idempotentHint=True,                # Same inputs = same outputs
    ),
    structured_output=True,                 # Return Pydantic model
)
def my_tool(arg: str) -> MyModel:
    """Docstring becomes the tool description."""
    pass
```

---

## Resource URI Schemes

- `file://` - Local file resources
- `resource://` - Custom resource identifier
- `http://` / `https://` - Web resources (if implemented)

---

## Transport Options

```python
# stdio (default) - for subprocess communication
mcp.run()
mcp.run(transport="stdio")

# HTTP - for network communication
mcp.run(transport="streamable-http")
```
