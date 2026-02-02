import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import (
    BlobResourceContents,
    Prompt,
    PromptMessage,
    Resource,
    ResourceTemplate,
    TextResourceContents,
)

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(
        self,
        name: str,
        command: str,
        server_args: list[str],
        env_vars: dict[str, str] = None,
    ) -> None:
        print(f"[DEBUG][MCPClient.__init__] Creating MCPClient: name={name}, command={command}")
        print(f"[DEBUG][MCPClient.__init__] server_args={server_args}")
        self.name = name
        self.command = command
        self.server_args = server_args
        self.env_vars = env_vars
        self._session: ClientSession = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._connected: bool = False
        print(f"[DEBUG][MCPClient.__init__] MCPClient initialized")

    async def connect(self) -> None:
        """
        Connect to the server set in the constructor.
        """
        print(f"[DEBUG][MCPClient.connect] Starting connection to server...")
        if self._connected:
            raise RuntimeError("Client is already connected")

        server_parameters = StdioServerParameters(
            command=self.command,
            args=self.server_args,
            env=self.env_vars if self.env_vars else None,
        )
        print(f"[DEBUG][MCPClient.connect] StdioServerParameters created")

        # Connect to stdio server, starting subprocess
        print(f"[DEBUG][MCPClient.connect] Connecting to stdio server (starting subprocess)...")
        stdio_connection = await self._exit_stack.enter_async_context(
            stdio_client(server_parameters)
        )
        self.read, self.write = stdio_connection
        print(f"[DEBUG][MCPClient.connect] Stdio connection established")

        # Start MCP client session
        print(f"[DEBUG][MCPClient.connect] Starting MCP client session...")
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream=self.read, write_stream=self.write)
        )

        # Initialize session
        print(f"[DEBUG][MCPClient.connect] Initializing session...")
        await self._session.initialize()
        self._connected = True
        print(f"[DEBUG][MCPClient.connect] Connection complete, session initialized")

    async def use_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> list[str]:
        print(f"[DEBUG][MCPClient.use_tool] Calling tool: {tool_name}")
        print(f"[DEBUG][MCPClient.use_tool] Arguments: {arguments}")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")

        tool_call_result = await self._session.call_tool(
            name=tool_name, arguments=arguments
        )
        logger.debug(f"Calling tool {tool_name} with arguments {arguments}")
        print(f"[DEBUG][MCPClient.use_tool] Tool call completed, processing results...")

        results = []
        if tool_call_result.content:
            for content in tool_call_result.content:
                print(f"[DEBUG][MCPClient.use_tool] Content type: {content.type}")
                match content.type:
                    case "text":
                        results.append(content.text)
                    case "image" | "audio":
                        results.append(content.data)
                    case "resource":
                        if isinstance(content.resource, TextResourceContents):
                            results.append(content.resource.text)
                        else:
                            results.append(content.resource.blob)
        else:
            logger.warning(f"No content in tool call result for tool {tool_name}")
        print(f"[DEBUG][MCPClient.use_tool] Returning {len(results)} result(s)")
        return results

    async def get_resource(
        self, uri: str
    ) -> list[BlobResourceContents | TextResourceContents]:
        print(f"[DEBUG][MCPClient.get_resource] Reading resource: {uri}")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")
        resource_read_result = await self._session.read_resource(uri=uri)

        if not resource_read_result.contents:
            logger.warning(f"No content read for resource URI {uri}")
        print(f"[DEBUG][MCPClient.get_resource] Retrieved {len(resource_read_result.contents)} content item(s)")
        return resource_read_result.contents

    async def load_prompt(
        self, name: str, arguments: dict[str, str]
    ) -> list[PromptMessage]:
        print(f"[DEBUG][MCPClient.load_prompt] Loading prompt: {name}")
        print(f"[DEBUG][MCPClient.load_prompt] Arguments: {arguments}")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")
        prompt_load_result = await self._session.get_prompt(
            name=name, arguments=arguments
        )

        if not prompt_load_result.messages:
            logger.warning(f"No prompt found for prompt {name}")
        else:
            logger.debug(
                f"Loaded prompt {name} with description {prompt_load_result.description}"
            )
        print(f"[DEBUG][MCPClient.load_prompt] Loaded {len(prompt_load_result.messages)} message(s)")
        return prompt_load_result.messages

    async def get_available_resources(self) -> list[Resource]:
        print(f"[DEBUG][MCPClient.get_available_resources] Listing available resources...")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")

        resources_result = await self._session.list_resources()
        if not resources_result.resources:
            logger.warning("No resources found on server")
        print(f"[DEBUG][MCPClient.get_available_resources] Found {len(resources_result.resources)} resource(s)")
        return resources_result.resources

    async def get_available_resource_templates(self) -> list[ResourceTemplate]:
        print(f"[DEBUG][MCPClient.get_available_resource_templates] Listing resource templates...")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")

        resource_templates_result = await self._session.list_resource_templates()
        if not resource_templates_result.resources:
            logger.warning("No resource templates found on server")
        print(f"[DEBUG][MCPClient.get_available_resource_templates] Found {len(resource_templates_result.resources)} template(s)")
        return resource_templates_result.resources

    async def get_available_tools(self) -> list[dict[str, Any]]:
        print(f"[DEBUG][MCPClient.get_available_tools] Listing available tools...")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")

        tools_result = await self._session.list_tools()
        if not tools_result.tools:
            logger.warning("No tools found on server")
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
        print(f"[DEBUG][MCPClient.get_available_tools] Found {len(available_tools)} tool(s): {[t['name'] for t in available_tools]}")
        return available_tools

    async def get_available_prompts(self) -> list[Prompt]:
        print(f"[DEBUG][MCPClient.get_available_prompts] Listing available prompts...")
        if not self._connected:
            raise RuntimeError("Client not connected to a server")

        prompt_result = await self._session.list_prompts()
        if not prompt_result.prompts:
            logger.warning("No prompts found on server")
        print(f"[DEBUG][MCPClient.get_available_prompts] Found {len(prompt_result.prompts)} prompt(s): {[p.name for p in prompt_result.prompts]}")
        return prompt_result.prompts

    async def disconnect(self) -> None:
        """
        Clean up any resources
        """
        print(f"[DEBUG][MCPClient.disconnect] Disconnecting from server...")
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._connected = False
            self._session = None
        print(f"[DEBUG][MCPClient.disconnect] Disconnected and cleaned up resources")
