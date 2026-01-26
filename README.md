# AI Agents with MCP - Code Examples

Welcome to the code repository for **AI Agents with MCP** (Model Context Protocol). This repository contains progressive code examples that demonstrate how to build AI agents that communicate with tools, resources, and prompts using the MCP standard.

## Overview

The Model Context Protocol (MCP) provides a standardized way for AI applications to connect with external tools and data sources. This repository walks you through building both MCP clients (hosts) and servers, from basic concepts to advanced features.

### Repository Structure

```
ai_agents_mcp_examples/
├── ch3/                    # Building MCP Clients (Host Applications)
├── ch4/                    # Advanced Client Features
├── ch5/                    # Building MCP Servers
├── ch6/                    # Advanced Server Features
├── pyproject.toml          # Project dependencies
└── README.md               # This file
```

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- An LLM API key (e.g., Anthropic API key)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai_agents_mcp_examples
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Set up your environment variables:
   ```bash
   # Copy the example env file in the chapter you're working with
   cp ch3/.env.example ch3/.env
   
   # Edit the .env file and add your API key
   # LLM_API_KEY=your-api-key-here
   ```

## Dependencies

This project uses the following main dependencies:

- **anthropic** - Anthropic's Python SDK for Claude
- **mcp[cli]** - Model Context Protocol SDK
- **pillow** - Image processing library
- **pydantic** - Data validation
- **python-dotenv** - Environment variable management

## Running Examples

All examples can be run using uv:

```bash
# Run a specific example
uv run ch3/01_host_no_client.py

# Run examples in subdirectories
uv run ch3/08_make_tool_calls/agent.py

# Run an MCP server
uv run ch3/calculator_server.py
```

## Chapter Overview

### Chapter 3: Building MCP Clients

Learn how to build host applications that connect to MCP servers. Topics include:
- Creating a basic LLM-powered assistant
- Building an MCP client interface
- Connecting to servers via stdio and HTTP transports
- Listing and calling tools
- Working with resources and prompts

### Chapter 4: Advanced Client Features

Explore advanced client capabilities:
- Handling server logging messages
- Implementing sampling callbacks
- Providing file roots to servers
- Processing elicitation requests
- Working with multiple LLM models
- Connecting to multiple MCP servers

### Chapter 5: Building MCP Servers

Learn to build MCP servers using FastMCP:
- Low-level server implementation
- Creating tools with structured output
- Building prompts (single and multi-turn)
- Exposing resources and resource templates
- Lifespan management

### Chapter 6: Advanced Server Features

Master advanced server concepts:
- Completions and server metadata
- Context object usage (server info, session, request, logging)
- Progress notifications
- Request cancellation
- Pagination
- Elicitations and sampling from server-side
- File system roots

## Code Structure

Each chapter contains numbered examples that build upon each other:

- **Standalone files** (e.g., `01_host_no_client.py`) - Single-file examples
- **Subdirectories** (e.g., `08_make_tool_calls/`) - Multi-file examples with:
  - `agent.py` - The host/agent application
  - `client.py` - The MCP client implementation
  - `server.py` - MCP server implementation (in ch5/ch6)

## Calculator Server

The `calculator_server.py` in chapters 3 and 4 provides a full-featured MCP server for testing, including:

- Mathematical operations (add, subtract, multiply, divide, power, square root)
- A prompt for calculation tasks
- A resource with mathematical constants
- Sampling and elicitation demonstrations

## License

See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
