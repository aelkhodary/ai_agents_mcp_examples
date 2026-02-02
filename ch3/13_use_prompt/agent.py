import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from client import MCPClient
from dotenv import load_dotenv
from mcp.types import TextResourceContents

load_dotenv()

LLM_API_KEY = os.environ["LLM_API_KEY"]
anthropic_client = Anthropic(api_key=LLM_API_KEY)
logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, mcp_client: MCPClient, anthropic_client: Anthropic):
        print(f"[DEBUG][Agent.__init__] Initializing Agent...")
        self.mcp_client = mcp_client
        self.anthropic_client = anthropic_client
        self.available_resources = {}
        self.available_prompts = {}
        print(f"[DEBUG][Agent.__init__] Agent initialized")

    async def _select_resources(self, user_query: str) -> list[str]:
        """Use LLM to intelligently select relevant resources."""
        print(f"[DEBUG][Agent._select_resources] Starting resource selection for query: '{user_query}'")
        if not self.available_resources:
            print(f"[DEBUG][Agent._select_resources] No resources available, returning empty list")
            return []

        resource_descriptions = {
            name: resource.description or f"Resource: {name}"
            for name, resource in self.available_resources.items()
        }
        print(f"[DEBUG][Agent._select_resources] resource_descriptions: {resource_descriptions}")

        selection_prompt = f"""
Given this user question: "{user_query}"

And these available resources:
{json.dumps(resource_descriptions, indent=2)}

Which resources (if any) would be helpful to answer the user's question?
Return a JSON array of resource names, or an empty array if no resources are needed.
Only include resources that are directly relevant.

Example: ["math-constants"] or []
"""

        try:
            print(f"[DEBUG][Agent._select_resources] Calling LLM to select resources...")
            response = self.anthropic_client.messages.create(
                max_tokens=200,
                messages=[{"role": "user", "content": selection_prompt}],
                model="claude-sonnet-4-0",
            )

            response_text = response.content[0].text.strip()
            print(f"[DEBUG][Agent._select_resources] LLM response: {response_text}")
            if "[" in response_text and "]" in response_text:
                start = response_text.find("[")
                end = response_text.rfind("]") + 1
                json_part = response_text[start:end]
                selected_resources = json.loads(json_part)
                result = [
                    r for r in selected_resources if r in self.available_resources
                ]
                print(f"[DEBUG][Agent._select_resources] Selected resources: {result}")
                return result

        except Exception as e:
            logger.warning(f"Failed to select resources with LLM: {e}")
            print(f"[DEBUG][Agent._select_resources] ERROR: {e}")

        print(f"[DEBUG][Agent._select_resources] Returning empty list (no resources selected)")
        return []

    async def _select_prompts(self, user_query: str) -> list[dict[str, Any]]:
        """Use LLM to intelligently select relevant prompts."""
        print(f"[DEBUG][Agent._select_prompts] Starting prompt selection for query: '{user_query}'")
        if not self.available_prompts:
            print(f"[DEBUG][Agent._select_prompts] No prompts available, returning empty list")
            return []

        prompts = [
            prompt.model_dump_json() for prompt in self.available_prompts.values()
        ]
        print(f"[DEBUG][Agent._select_prompts] Available prompts: {list(self.available_prompts.keys())}")

        selection_prompt = f"""
Given this user question: "{user_query}"

And these available prompt templates:
{json.dumps(prompts, indent=2)}

Which prompts (if any) would provide helpful instructions or guidance for answering this question?
Return a JSON array of prompt objects which have a name (string) and arguments (objects where the 
keys are the named parameter name and value is the argument value), or an empty array if no prompts
are needed. Only include prompts that are directly relevant.

Example: [{{"name": "calculation-helper", "arguments": {{"operation": "addition"}}]}},
 {{"name": "step-by-step-math", "arguments": {{}}}}] or []
"""

        try:
            print(f"[DEBUG][Agent._select_prompts] Calling LLM to select prompts...")
            response = self.anthropic_client.messages.create(
                max_tokens=200,
                messages=[{"role": "user", "content": selection_prompt}],
                model="claude-sonnet-4-0",
            )

            response_text = response.content[0].text.strip()
            print(f"[DEBUG][Agent._select_prompts] LLM response: {response_text}")
            if "[" in response_text and "]" in response_text:
                start = response_text.find("[")
                end = response_text.rfind("]") + 1
                json_part = response_text[start:end]
                selected_prompts = json.loads(json_part)
                result = [
                    p
                    for p in selected_prompts
                    if p["name"] in self.available_prompts
                ]
                print(f"[DEBUG][Agent._select_prompts] Selected prompts: {result}")
                return result

        except Exception as e:
            logger.warning(f"Failed to select prompts with LLM: {e}")
            print(f"[DEBUG][Agent._select_prompts] ERROR: {e}")

        print(f"[DEBUG][Agent._select_prompts] Returning empty list (no prompts selected)")
        return []

    async def _load_selected_resources(
        self, resource_names: list[str]
    ) -> list[dict[str, Any]]:
        """Load the specified resources."""
        print(f"[DEBUG][Agent._load_selected_resources] Loading {len(resource_names)} resource(s): {resource_names}")
        context_messages = []

        for resource_name in resource_names:
            print(f"[DEBUG][Agent._load_selected_resources] Processing resource: {resource_name}")
            if resource_name in self.available_resources:
                print(f"LLM selected resource: {resource_name}")
                try:
                    resource = self.available_resources[resource_name]
                    resource_contents = await self.mcp_client.get_resource(
                        uri=resource.uri
                    )
                    for content in resource_contents:
                        if isinstance(content, TextResourceContents):
                            context_messages.append(
                                {
                                    "type": "text",
                                    "text": f"[Resource: {resource_name}]\n{content.text}",
                                }
                            )
                        elif content.mimeType in [
                            "image/jpeg",
                            "image/png",
                            "image/gif",
                            "image/webp",
                        ]:  # b64-encoded image
                            context_messages.append(
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": content.mimeType,
                                        "data": content.blob,
                                    },
                                }
                            )
                        else:
                            print(
                                f"WARNING: Unable to process mimeType {resource_contents.mimeType} for resource {resource_name}"
                            )
                except Exception as e:
                    print(f"[DEBUG][Agent._load_selected_resources] Error loading resource {resource_name}: {e}")

        print(f"[DEBUG][Agent._load_selected_resources] Returning {len(context_messages)} context message(s)")
        return context_messages

    async def _load_selected_prompts(self, prompts: list[dict[str, Any]]) -> str:
        """Load the specified prompts as system instructions."""
        print(f"[DEBUG][Agent._load_selected_prompts] Loading {len(prompts)} prompt(s)")
        system_instructions = []

        for prompt in prompts:
            if prompt["name"] in self.available_prompts:
                print(f"[DEBUG][Agent._load_selected_prompts] Loading prompt: {prompt['name']} with args: {prompt.get('arguments', {})}")
                try:
                    prompt_content = await self.mcp_client.load_prompt(
                        name=prompt["name"], arguments=prompt["arguments"]
                    )

                    # Extract the prompt text
                    prompt_text = ""
                    for message in prompt_content:
                        if hasattr(message.content, "text"):
                            prompt_text += message.content.text + "\n"
                        elif isinstance(message.content, str):
                            prompt_text += message.content + "\n"

                    if prompt_text.strip():
                        system_instructions.append(
                            f"[Prompt: {prompt['name']}]\n{prompt_text.strip()}"
                        )

                except Exception as e:
                    print(f"[DEBUG][Agent._load_selected_prompts] Error loading prompt {prompt['name']}: {e}")

        print(f"[DEBUG][Agent._load_selected_prompts] Returning {len(system_instructions)} system instruction(s)")
        return "\n\n".join(system_instructions)

    async def _refresh(self) -> None:
        print(f"[DEBUG][Agent._refresh] Refreshing available resources and prompts...")
        available_resources = await self.mcp_client.get_available_resources()
        self.available_resources = {
            resource.name: resource for resource in available_resources
        }
        print(f"[DEBUG][Agent._refresh] Cached {len(self.available_resources)} resource(s)")
        available_prompts = await self.mcp_client.get_available_prompts()
        self.available_prompts = {
            prompt.name: prompt for prompt in available_prompts
        }
        print(f"[DEBUG][Agent._refresh] Cached {len(self.available_prompts)} prompt(s)")

    async def run(self):
        print(f"[DEBUG][Agent.run] ========== AGENT RUN STARTING ==========")
        try:
            print(
                "Welcome to your AI Assistant. Type 'goodbye' to quit or 'refresh' to reload and redisplay available resources."
            )
            print(f"[DEBUG][Agent.run] Connecting to MCP server...")
            await self.mcp_client.connect()
            print(f"[DEBUG][Agent.run] Getting available tools...")
            available_tools = await self.mcp_client.get_available_tools()
            print(f"[DEBUG][Agent.run] Refreshing resources and prompts...")
            await self._refresh()

            print(
                f"Loaded {len(self.available_resources)} resources and {len(self.available_prompts)} prompts"
            )
            print(f"[DEBUG][Agent.run] Setup complete, entering main loop...")

            while True:
                print(f"\n[DEBUG][Agent.run] -------- NEW USER INPUT CYCLE --------")
                prompt = input("You: ")
                print(f"[DEBUG][Agent.run] User input received: '{prompt}'")

                if prompt.lower() == "goodbye":
                    print(f"[DEBUG][Agent.run] Goodbye command received, exiting...")
                    print("AI Assistant: Goodbye!")
                    break

                if prompt.lower() == "refresh":
                    print(f"[DEBUG][Agent.run] Refresh command received")
                    await self._refresh()
                    continue

                # Select relevant resources and prompts
                print(f"[DEBUG][Agent.run] Step 1: Selecting relevant resources...")
                selected_resource_names = await self._select_resources(prompt)
                print(f"[DEBUG][Agent.run] Step 2: Selecting relevant prompts...")
                selected_prompt_names = await self._select_prompts(prompt)

                # Load relevant resources and prompts
                print(f"[DEBUG][Agent.run] Step 3: Loading selected resources...")
                context_messages = await self._load_selected_resources(
                    selected_resource_names
                )
                print(f"[DEBUG][Agent.run] Step 4: Loading selected prompts...")
                system_instructions = await self._load_selected_prompts(
                    selected_prompt_names
                )

                # Build conversation with initial user message and any context
                print(f"[DEBUG][Agent.run] Step 5: Building conversation messages...")
                user_content = [{"type": "text", "text": prompt}]
                if context_messages:
                    print(f"[DEBUG][Agent.run] Adding {len(context_messages)} context message(s) to user content")
                    user_content.extend(context_messages)

                conversation_messages = [{"role": "user", "content": user_content}]
                print(f"[DEBUG][Agent.run] Conversation initialized with {len(conversation_messages)} message(s)")

                # Tool use loop - continue until we get a final text response
                print(f"[DEBUG][Agent.run] Step 6: Entering tool use loop...")
                tool_loop_iteration = 0
                while True:
                    tool_loop_iteration += 1
                    print(f"[DEBUG][Agent.run] Tool loop iteration #{tool_loop_iteration}")
                    
                    create_message_args = {
                        "max_tokens": 4096,
                        "messages": conversation_messages,
                        "model": "claude-sonnet-4-0",
                        "tools": available_tools,
                        "tool_choice": {"type": "auto"},
                    }

                    if system_instructions:
                        print(f"[DEBUG][Agent.run] Adding system instructions to LLM call")
                        create_message_args["system"] = system_instructions

                    print(f"[DEBUG][Agent.run] Calling Anthropic API...")
                    current_response = self.anthropic_client.messages.create(
                        **create_message_args
                    )
                    print(f"[DEBUG][Agent.run] LLM response received, stop_reason: {current_response.stop_reason}")

                    # Add assistant message to conversation
                    conversation_messages.append(
                        {"role": "assistant", "content": current_response.content}
                    )
                    print(f"[DEBUG][Agent.run] Added assistant response to conversation")

                    # Check if we need to use tools
                    if current_response.stop_reason == "tool_use":
                        print(f"[DEBUG][Agent.run] LLM requested tool use")
                        # Extract tool use blocks
                        tool_use_blocks = [
                            block
                            for block in current_response.content
                            if block.type == "tool_use"
                        ]
                        print(f"[DEBUG][Agent.run] Found {len(tool_use_blocks)} tool use block(s)")

                        # Execute all tools and collect results
                        tool_results = []
                        for i, tool_use in enumerate(tool_use_blocks):
                            print(f"[DEBUG][Agent.run] Executing tool {i+1}/{len(tool_use_blocks)}: {tool_use.name}")
                            print(f"[DEBUG][Agent.run] Tool input: {tool_use.input}")
                            tool_result = await self.mcp_client.use_tool(
                                tool_name=tool_use.name, arguments=tool_use.input
                            )
                            print(f"[DEBUG][Agent.run] Tool result: {tool_result}")
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use.id,
                                    "content": "\n".join(tool_result),
                                }
                            )

                        # Add tool results to conversation
                        conversation_messages.append(
                            {"role": "user", "content": tool_results}
                        )
                        print(f"[DEBUG][Agent.run] Added tool results to conversation, continuing loop...")

                        # Continue loop to get next LLM response
                        continue

                    else:
                        # No tools needed, extract final text response
                        print(f"[DEBUG][Agent.run] No tool use needed, extracting final response...")
                        text_blocks = [
                            content.text
                            for content in current_response.content
                            if hasattr(content, "text") and content.text.strip()
                        ]

                        if text_blocks:
                            print(f"[DEBUG][Agent.run] Found {len(text_blocks)} text block(s)")
                            print(f"Assistant: {text_blocks[0]}")
                        else:
                            print(f"[DEBUG][Agent.run] No text blocks found in response")
                            print("Assistant: [No text response available]")

                        # Exit the tool use loop
                        print(f"[DEBUG][Agent.run] Exiting tool use loop")
                        break
        finally:
            print(f"[DEBUG][Agent.run] ========== CLEANUP ==========")
            await self.mcp_client.disconnect()
            print(f"[DEBUG][Agent.run] ========== AGENT RUN COMPLETE ==========")


if __name__ == "__main__":
    print(f"[DEBUG][main] ========== PROGRAM STARTING ==========")
    print(f"[DEBUG][main] Creating MCPClient...")
    mcp_client = MCPClient(
        name="calculator_server_connection",
        command="uv",
        server_args=[
            "--directory",
            str(Path(__file__).parent.parent.resolve()),
            "run",
            "calculator_server.py",
        ],
    )
    print(f"[DEBUG][main] Creating Agent...")
    agent = Agent(mcp_client, anthropic_client)
    print(f"[DEBUG][main] Running agent...")
    asyncio.run(agent.run())
    print(f"[DEBUG][main] ========== PROGRAM COMPLETE ==========")
