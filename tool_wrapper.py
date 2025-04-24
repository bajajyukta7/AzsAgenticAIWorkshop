from autogen_core.tools import FunctionTool
import logging
import shutil
import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

class ToolWrapper:
    """Manages multiple tools and provides dynamic tool selection."""
    

    

    def create_azure_vm(cli_command: str, subscription_id: str):
        """
        Authenticates using Azure CLI, sets the subscription, and executes the VM creation command.
        Returns the VM's resource ID on success.

        Parameters:
        - cli_command (str): Azure CLI command to create the VM and return its ID.
        - subscription_id (str): Azure subscription ID to set context.

        Returns:
        - resource_id (str | None): Azure resource ID of the created VM
        - error (str | None): Error message if creation fails
        """

        import subprocess

        az = shutil.which("az")

        try:
            result = subprocess.run([az, "--version"], capture_output=True, text=True, check=True)
            print("✅ AZ CLI is working!")
            print(result.stdout)
        except FileNotFoundError:
            print("❌ Azure CLI (az) not found. Check your PATH or install it.")
        except subprocess.CalledProcessError as e:
            print("❌ Azure CLI command failed:")
            print(e.stderr)

        try:
            # Step 1: Authenticate (interactive login)
            print("Entered Create Azure VM Function\n")
            subprocess.run([az, "login"], check=True)
            print("Azure CLI login succeeded.\n")

            # Step 2: Set subscription
            set_subscription_cmd = [az, "account", "set", "--subscription", subscription_id]
            subprocess.run(set_subscription_cmd, check=True)
            print(f"Azure CLI subscription set to: {subscription_id}\n")

            # Step 3: Execute VM creation command
            completed_process = subprocess.run(
                cli_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )

            resource_id = completed_process.stdout.strip()
            print("VM creation succeeded.")
            print(f"VM Resource ID: {resource_id}")
            return resource_id, None

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip()
            logging.error("VM creation failed.")
            logging.debug(f"Error Output:\n{error_output}")
            return None, error_output

    @staticmethod
    def get_create_azure_vm():
        execution_tool = FunctionTool(
            ToolWrapper.create_azure_vm,
            description="Execute azure cli commands to create virtual machine",
        )
        return execution_tool
    

    @staticmethod
    def rag_retriever_tool(user_input:str) -> str :
        
        index_name = "visindex"
        
        print("Retrieving from azure search for user input:\n", user_input)
        
        search_endpoint = os.getenv("SEARCH_ENDPOINT", "https://ybazscognitivesearchservice.search.windows.net")  
        search_key = os.getenv("AZ_OPENAI_API_SEARCH_KEY")   
        print(search_key,"\n")
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_key)
        )

        docs = ""
        docs = list(search_client.search(user_input))
        doc_content = "retriever data:"
        # Append retrieved documents as context
        if docs:
            doc_content = "\n".join([doc["content"] for doc in docs])

        print("Retrieved doc content:\n\n\n ", doc_content)
        return doc_content

    @staticmethod
    def get_retrieval_tool():
        retrieval_tool = FunctionTool(
            ToolWrapper.rag_retriever_tool,
            description="Fetch the relevant documents for a user query from RAG database.",
        )
        return retrieval_tool