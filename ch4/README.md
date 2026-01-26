# Chapter 4: Advanced Client Features

This chapter explores advanced MCP client capabilities including logging, sampling, roots, elicitations, and working with multiple servers and models.

## Prerequisites

1. Copy the environment example and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and set LLM_API_KEY=your-api-key
   ```

## Examples Overview

### 01. Handle Logging (`01_handle_logging/`)

Implements a logging callback to receive and display log messages from the MCP server.

```bash
uv run ch4/01_handle_logging/agent.py
```

**Key Concepts:**
- `LoggingMessageNotificationParams` handling
- `logging_callback` parameter in `ClientSession`
- Log levels: debug, info, warning, error, critical, alert, emergency

**Implementation:**
```python
async def _handle_logs(self, params: LoggingMessageNotificationParams) -> None:
    if params.level in ("info", "error", "critical", "alert", "emergency"):
        print(f"[{params.level}] - {params.data}")

# In connect():
ClientSession(
    read_stream=self.read,
    write_stream=self.write,
    logging_callback=self._handle_logs,
)
```

---

### 02. Sampling Callback (`02_sampling_callback/`)

Implements the sampling callback to handle server-initiated LLM requests.

```bash
uv run ch4/02_sampling_callback/agent.py
```

**Key Concepts:**
- `CreateMessageRequestParams` and `CreateMessageResult`
- Server-initiated LLM calls (sampling)
- `SamplingFnT` protocol

**Use Case:** When a server tool needs to call an LLM to complete its task (e.g., `explain_math` tool).

**Implementation:**
```python
async def _handle_sampling(
    self,
    context: RequestContext[ClientSession, None],
    params: CreateMessageRequestParams,
) -> CreateMessageResult | ErrorData:
    # Forward the request to your LLM
    response = self._llm_client.messages.create(
        max_tokens=params.maxTokens,
        messages=messages,
        model="claude-sonnet-4-0",
    )
    return CreateMessageResult(
        role=response.role,
        content=content_data,
        model="claude-sonnet-4-0"
    )
```

---

### 03. Providing Roots (`03_providing_roots/`)

Implements the roots callback to provide file system access boundaries to the server.

```bash
uv run ch4/03_providing_roots/agent.py
```

**Key Concepts:**
- `ListRootsResult` and `Root` types
- `RootsFnT` protocol
- File system sandboxing

**Use Case:** Server tools that need file system access (e.g., `count_files`) can only access paths within provided roots.

**Implementation:**
```python
async def _handle_roots(
    self,
    context: RequestContext[ClientSession, Any],
) -> ListRootsResult | ErrorData:
    roots_result = []
    for root in self.file_roots:
        roots_result.append(Root(uri=root))  # e.g., "file:///path/to/dir"
    return ListRootsResult(roots=roots_result)
```

---

### 04. Returning Elicitations (`04_returning_elicitations/`)

Implements the elicitation callback to handle server requests for user input.

```bash
uv run ch4/04_returning_elicitations/agent.py
```

**Key Concepts:**
- `ElicitRequestParams` and `ElicitResult`
- JSON Schema for form validation
- User actions: accept, decline, cancel

**Use Case:** When a server tool needs to collect structured data from the user (e.g., `signup_math_facts`).

**Implementation:**
```python
async def _handle_elicitation(
    self,
    context: RequestContext[ClientSession, Any],
    params: ElicitRequestParams,
) -> ElicitResult | ErrorData:
    # Display params.message to user
    # Collect form data based on params.requestedSchema
    
    if user_accepts:
        return ElicitResult(action="accept", content=form_data)
    elif user_declines:
        return ElicitResult(action="decline")
    else:
        return ElicitResult(action="cancel")
```

---

### 05. Multiple Models (`05_multiple_models/`)

Demonstrates using different LLM models for different purposes.

```bash
uv run ch4/05_multiple_models/agent.py
```

**Key Concepts:**
- Model selection strategies
- Cost/performance trade-offs
- Using faster models for resource/prompt selection

**Files:**
- `agent.py` - Agent with multi-model support
- `client.py` - MCP client
- `internal_tool.py` - Internal tool helpers

---

### 06. Multiple Servers (`06_multiple_servers/`)

Connects to and manages multiple MCP servers simultaneously.

```bash
uv run ch4/06_multiple_servers/agent.py
```

**Key Concepts:**
- Managing multiple `ClientSession` instances
- Tool routing to correct server
- Resource aggregation across servers

**Architecture:**
```python
class MCPClient:
    def __init__(self, name: str, llm_client: Anthropic, file_roots: list[str]):
        self._servers: dict[str, ClientSession] = {}
    
    async def connect(self, server_parameters: StdioServerParameters):
        # Add server to managed connections
        
    async def use_tool(self, tool_name: str, arguments: dict):
        # Route to correct server based on tool name
```

---

## Calculator Server (`calculator_server.py`)

Same as Chapter 3, provides a comprehensive MCP server for testing all client features.

---

## Key Callback Protocols

### LoggingFnT
Receives log messages from the server:
```python
async def callback(params: LoggingMessageNotificationParams) -> None
```

### SamplingFnT
Handles server-initiated LLM requests:
```python
async def callback(
    context: RequestContext[ClientSession, None],
    params: CreateMessageRequestParams
) -> CreateMessageResult | ErrorData
```

### RootsFnT
Provides file system roots to the server:
```python
async def callback(
    context: RequestContext[ClientSession, Any]
) -> ListRootsResult | ErrorData
```

### ElicitFnT
Handles server requests for user input:
```python
async def callback(
    context: RequestContext[ClientSession, Any],
    params: ElicitRequestParams
) -> ElicitResult | ErrorData
```

---

## Complete ClientSession Initialization

```python
self._session = await self._exit_stack.enter_async_context(
    ClientSession(
        read_stream=self.read,
        write_stream=self.write,
        logging_callback=self._handle_logs,
        sampling_callback=self._handle_sampling,
        list_roots_callback=self._handle_roots,
        elicitation_callback=self._handle_elicitation,
    ),
)
```

---

## Best Practices

1. **Logging** - Always implement logging callback for debugging
2. **Sampling** - Required if server tools use LLM capabilities
3. **Roots** - Essential for file system security
4. **Elicitations** - Provide good UX for user input collection
5. **Multiple Servers** - Use tool namespacing to avoid conflicts
