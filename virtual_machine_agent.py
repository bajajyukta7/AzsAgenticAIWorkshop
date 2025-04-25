from tool_wrapper import ToolWrapper
# import user_proxy_agent

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_core import RoutedAgent
from autogen_agentchat.messages import HandoffMessage

# Global variables
retriever = None
agent = None
system_message = None

from autogen_core import CancellationToken
from autogen_agentchat.messages import BaseMessage
from autogen_agentchat.messages import (
    TextMessage
)

from autogen_agentchat.base import Response
from autogen_agentchat.messages import ToolCallExecutionEvent
from agent_utility import AgentWrapper
from tool_wrapper import ToolWrapper



class VirtualMachineAgent():
    @staticmethod
    def get_agent(model_client, tools=[]):
        system_prompt = """
        You are an assistant designed to help create Azure virtual machines or virtual instance for sap solutions.
        Your task is to generate a azure cli command that can be used to create an Azure resource based on user inputs required in azure cli command.
        Once azure cli is generated, wait for user to confirm if they want to create azure resources.
        Once the create azure vm is called, wrap azure cli command inside a call to the function create_azure_vm, which takes the full azure cli command as a string argument.
        Don't repeat the response and don't confuse virtual machine and virtual instance for sap solutions.
        Think before responding.
        """
        system_prompt_with_rag = """
        You are an assistant designed to help create Azure virtual machines or virtual instance for sap solutions.
        Your task is to generate a azure cli command that can be used to create an Azure resource based on user inputs required in azure cli command.
        Once azure cli is generated, wait for user to confirm if they want to create azure resources.
        Once the create azure vm is called, wrap azure cli command inside a call to the function create_azure_vm, which takes the full azure cli command as a string argument.
        To create virtual instance for sap solutions, use rag_retriever_tool to get azure cli command.
        Don't repeat the response and don't confuse virtual machine and virtual instance for sap solutions.
        Think before responding.
        """

        # print("tools: ", tools)
        # Initialize Assistant Agent
        virtual_machine_agent = AssistantAgent(
            name="AzureResourceAgent",
            tools=tools,
            model_client=model_client,
            system_message=system_prompt,
            handoffs=["user"],
            reflect_on_tool_use = True
        )
        
        return virtual_machine_agent

    @staticmethod
    async def chat_with_agent(user_input):

        # if not input_prompt or not isinstance(input_prompt, str):
        #     raise ValueError("❌ Invalid input: Message must be a non-empty string.")
        messages = []
        # Convert conversation history into formatted messages
        for message in user_input:
            role = message.get("role", "").capitalize()  # Ensure proper casing (User/Assistant)
            content = message.get("content", "")
            messages.append(f"{role}: {content}")

            # Extract latest user message for context retrieval
            # latest_user_message = user_input[-1].get("content", "")
        latest_user_message = user_input[-1].get("content", "")
        print("Starting chat with input:", messages)
        messages_string = "\n".join(messages)

        agent = VirtualMachineAgent.get_agent(AgentWrapper.get_model_client(),
                                              ToolWrapper.get_all_tools())  # ✅ Get the GroupChatManager

        # Process the response
        tools = []

        role_responses = {}  # Dictionary to store responses grouped by role
        tool_names = []  # List to store tool names

        async for response in agent.run_stream(task=messages_string):
            print(response)

            # Process text responses
            if isinstance(response, TextMessage) and response.content and response.source != "user":
                if response.source not in role_responses:
                    role_responses[response.source] = []
                if response.content not in role_responses[response.source]:  # Avoid duplicates
                    role_responses[response.source].append(response.content)

            # Process tool execution events
            if isinstance(response, ToolCallExecutionEvent):
                tools.append(response)  # Store tool execution events
                tool_names.extend([
                    content.name for content in response.content
                    if hasattr(content, "name") and not content.name.startswith("transfer_to_")
                ])
                print("Extracted Tool Names:", tool_names)

        # Prepare formatted responses
        all_responses = ""
        for role, contents in role_responses.items():
            all_responses += f"**🔹 {role.capitalize()}**: {' '.join(contents)}\n\n"

        # Add tools used to the output if any
        if tool_names:
            all_responses += f"**🛠 Tools Used:** {', '.join(tool_names)}"

        return all_responses