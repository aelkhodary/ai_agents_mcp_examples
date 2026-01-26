# Chapter 3: Building MCP Clients

This chapter teaches you how to build host applications (MCP clients) that connect to MCP servers and integrate with LLMs to create AI agents with tool-use capabilities.

## Prerequisites

1. Copy the environment example and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and set LLM_API_KEY=your-api-key
   ```

## Examples Overview

The examples in this chapter progressively build a complete MCP client implementation.

### 01. Host Without Client (`01_host_no_client.py`)

A basic AI assistant using the Anthropic API without any MCP integration. This establishes the baseline for comparison.

```bash
uv run ch3/01_host_no_client.py
```

**Key Concepts:**
- Basic LLM interaction with Claude
- Simple chat loop pattern

---

### 02. Host with Client Interface (`02_host_w_client_interface/`)

Introduces the `MCPClient` class interface with placeholder methods.

```bash
uv run ch3/02_host_w_client_interface/agent.py
```

**Files:**
- `agent.py` - Host application
- `client.py` - MCPClient interface definition

---

### 03. Stdio Client Constructor (`03_stdio_client_constructor/`)

Implements the MCPClient constructor with stdio server parameters.

**Key Concepts:**
- `StdioServerParameters` configuration
- Client initialization

---

### 04. Connect/Disconnect Stdio (`04_connect_disconnect_stdio/`)

Implements connection management for stdio-based MCP servers.

**Key Concepts:**
- Async context management with `AsyncExitStack`
- `ClientSession` initialization
- Proper resource cleanup

---

### 04a. Streamable HTTP Client (`04a_streamable_http_client_constructor/`)

Alternative transport using HTTP instead of stdio.

**Key Concepts:**
- HTTP-based MCP communication
- `streamablehttp_client` usage

---

### 04b. HTTP Connect/Disconnect (`04b_streamable_http_connect_disconnect/`)

Connection management for HTTP transport.

---

### 05. Instantiate Stdio Client (`05_instantiate_stdio_client/`)

Complete stdio client instantiation with working connection.

```bash
uv run ch3/05_instantiate_stdio_client/agent.py
```

---

### 06. Wrap List Tools (`06_wrap_list_tools/`)

Implements `get_available_tools()` to retrieve tools from the server.

**Key Concepts:**
- `session.list_tools()` API
- Tool schema format (name, description, input_schema)

---

### 07. Implement Use Tool (`07_implement_use_tool/`)

Implements `use_tool()` to execute tools on the server.

```bash
uv run ch3/07_implement_use_tool/agent.py
```

**Key Concepts:**
- `session.call_tool()` API
- Handling different content types (text, image, audio, resource)

---

### 08. Make Tool Calls (`08_make_tool_calls/`)

Complete tool-use loop integration with the LLM.

```bash
uv run ch3/08_make_tool_calls/agent.py
```

**Key Concepts:**
- Tool-use loop pattern
- Handling `stop_reason == "tool_use"`
- Building conversation with tool results

---

### 09. Wrap List Resources (`09_wrap_list_resources/`)

Implements `get_available_resources()` to discover server resources.

**Key Concepts:**
- `session.list_resources()` API
- Resource and ResourceTemplate types

---

### 10. Get Resource (`10_get_resource/`)

Implements `get_resource()` to read resource contents.

**Key Concepts:**
- `session.read_resource()` API
- TextResourceContents and BlobResourceContents

---

### 11. Use Resource (`11_use_resource/`)

Integrates resources into the agent conversation.

**Key Concepts:**
- Including resource content in LLM context
- Resource selection logic

---

### 12. Get Available Prompts (`12_get_available_prompts/`)

Implements `get_available_prompts()` to list server prompts.

**Key Concepts:**
- `session.list_prompts()` API
- Prompt metadata

---

### 13. Use Prompt (`13_use_prompt/`)

Implements `load_prompt()` and uses prompts in conversations.

```bash
uv run ch3/13_use_prompt/agent.py
```

**Key Concepts:**
- `session.get_prompt()` API
- PromptMessage format
- Using prompts as system instructions

---

## Calculator Server (`calculator_server.py`)

A comprehensive MCP server used for testing throughout this chapter.

**Tools:**
- `add`, `subtract`, `multiply`, `divide` - Basic arithmetic
- `power`, `square_root` - Advanced math
- `count_rs` - String manipulation
- `explain_math` - Uses sampling to explain operations
- `signup_math_facts` - Demonstrates elicitation
- `count_files` - File system access with roots

**Prompt:**
- `calculate_operation` - Guides calculation tasks

**Resource:**
- `resource://math-constants` - Mathematical constants (π, e, τ, etc.)

Run the server standalone:
```bash
uv run ch3/calculator_server.py
```

---

## Full Example (`full_example.py`)

The culmination of all concepts in a single complete implementation.

---

## Key MCP Client Concepts

### Transport Types
- **stdio** - Communication via standard input/output (subprocess)
- **HTTP (Streamable)** - Communication via HTTP requests

### Core Operations
1. **Connect** - Establish session with server
2. **List Tools** - Discover available tools
3. **Call Tool** - Execute a tool with arguments
4. **List Resources** - Discover available resources
5. **Read Resource** - Get resource contents
6. **List Prompts** - Discover available prompts
7. **Get Prompt** - Load a prompt template
8. **Disconnect** - Clean up resources

### Tool-Use Loop Pattern
```python
while True:
    response = llm.messages.create(tools=available_tools, ...)
    
    if response.stop_reason == "tool_use":
        # Execute tools and add results to conversation
        for tool_use in response.content:
            result = await client.use_tool(tool_use.name, tool_use.input)
            # Add result to conversation
        continue
    else:
        # Final response - exit loop
        break
```
