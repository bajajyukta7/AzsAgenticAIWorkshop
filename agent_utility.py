import os
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from tool_wrapper import ToolWrapper
from autogen_core.tools import FunctionTool, Tool
from autogen_core.models import AssistantMessage, FunctionExecutionResult, FunctionExecutionResultMessage, UserMessage

# Utility class for agents
class AgentWrapper:
    
    # This function can be moved to a base class from where agents will inherit.
    @staticmethod
    def get_model_client():
        
        
        # Azure OpenAI Deployment Configurations
        deployment_name = os.getenv("DEPLOYMENT_NAME", "gpt-4o")  
        azure_openai_api_version = "2025-01-01-preview"
        azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")  
        azure_openai_endpoint = os.getenv("ENDPOINT_URL")  

        az_model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=deployment_name,
            model=deployment_name,
            api_version=azure_openai_api_version,
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key # For key-based authentication.
        )
        return az_model_client