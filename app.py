import streamlit as st
import streamlit_mermaid as stmd
import os
import dotenv
import uuid
import traceback
import asyncio
import re
from virtual_machine_agent import VirtualMachineAgent
import time

# Load environment variables
dotenv.load_dotenv()

# Set Streamlit page configuration
st.set_page_config(
    page_title="AzS Workshop Agent",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Header ---
st.html("""<h2 style="text-align: center;">📚🔍 <i> AzS Workshop Agent </i> 🤖💬</h2>""")

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""
if "last_response" not in st.session_state:
    st.session_state.last_response = ""
if "last_cli_command" not in st.session_state:
    st.session_state.last_cli_command = ""

# Sidebar for API tokens and model selection
with st.sidebar:
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    st.session_state.AZURE_OPENAI_API_KEY = AZURE_OPENAI_API_KEY
    st.divider()
    models = ["azure-openai/gpt-4o"]
    st.selectbox("🤖 Select a Model", options=models, key="model")
    # st.button("Clear Chat", on_click=lambda: st.session_state.messages.clear(), type="primary")

    st.button(
       "Clear Chat", 
        on_click=lambda: (
           st.session_state.messages.clear(),
           st.session_state.update({"last_cli_command": ""})
    ), 
    type="primary"
    )

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def extract_cli_command(response):
    if "```bash" in response or "```" in response or "az cli" in response:  # Look for any CLI command wrapped in a code block
        # Extracting everything between ```bash or ``` (CLI code block)
        return response.split("```")[1].strip()
    return None

# Chat input
if prompt := st.chat_input("Your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.last_prompt = prompt

    with st.chat_message("assistant"):
        try:
            response = asyncio.run(VirtualMachineAgent.chat_with_agent(st.session_state.messages))
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.last_response = response

            # Extract CLI command if present
            cli_command = extract_cli_command(response)
            st.session_state.last_cli_command = cli_command

            st.markdown(response)
        except Exception as e:
            error_message = f"⚠️ Error generating response: {str(e)}"
            traceback.print_exc()
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            st.session_state.last_response = None
            st.error(error_message)

# --- Execute PowerShell Button ---
if st.session_state.last_cli_command:
    st.markdown("### Detected CLI Command:")
    st.code(st.session_state.last_cli_command, language="cli")
   
    if st.button("⚡ Create Azure Resource"):
        st.session_state.messages.append({"role": "user", "content": "Create virtual machine"})
        with st.chat_message("assistant"):
            try:
                response = asyncio.run(VirtualMachineAgent.chat_with_agent(st.session_state.messages))
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.last_response = response

                st.markdown(response)
            except Exception as e:
                error_message = f"⚠️ Error generating response: {str(e)}"
                traceback.print_exc()
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.session_state.last_response = None
                st.error(error_message)

# --- Regenerate Response Button ---
if st.session_state.get("last_prompt"):
    if st.button("🔄 Regenerate Response"):
        # Remove last assistant message
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.session_state.messages.pop()

        # Reprocess the last user prompt
        st.session_state.messages.append({"role": "user", "content": st.session_state.last_prompt})

        with st.chat_message("user"):
            st.markdown(st.session_state.last_prompt)

        with st.chat_message("assistant"):
            try:
                new_response = asyncio.run(VirtualMachineAgent.chat_with_agent(st.session_state.messages))
                st.session_state.messages.append({"role": "assistant", "content": new_response})
                st.session_state.last_response = new_response

                # Check for Mermaid diagram
                if "```mermaid" in new_response:
                    mermaid_code = new_response.split("```mermaid")[1].split("```")[0].strip()
                    stmd.st_mermaid(mermaid_code)

                st.markdown(new_response)
            except Exception as e:
                error_message = f"⚠️ Error generating response: {str(e)}"
                traceback.print_exc()
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.session_state.last_response = None
                st.error(error_message)
