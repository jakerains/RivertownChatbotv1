import streamlit as st
from bedrock_utils import init_bedrock, get_response_with_rag

# Initialize Bedrock clients
bedrock_client, runtime_client = init_bedrock()

# Set page config
st.set_page_config(page_title="Amazon Bedrock Chat", page_icon="🤖")
st.title("💬 Amazon Bedrock Chatbot with RAG")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        with st.spinner("Thinking..."):
            for response_chunk in get_response_with_rag(bedrock_client, runtime_client, prompt):
                full_response += response_chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response}) 