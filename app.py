import streamlit as st
from bedrock_utils import init_bedrock, get_response_with_rag
from dynamo_utils import init_dynamodb

# Initialize Bedrock clients
bedrock_client, runtime_client = init_bedrock()
dynamodb = init_dynamodb()

# Set page config
st.set_page_config(page_title="Amazon Bedrock Chat", page_icon="🤖")
st.title("💬 Amazon Bedrock Chatbot with RAG")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "phone_number" not in st.session_state:
    st.session_state.phone_number = None
if "cs_mode" not in st.session_state:
    st.session_state.cs_mode = False

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
        
        # Check for CS keywords or if we're already in CS mode
        cs_keywords = [
            'speak to someone',
            'talk to a person', 
            'customer service',
            'representative',
            'speak to a human',
            'talk to someone',
            'call me',
            'contact me'
        ]
        
        # Enter CS mode if keywords detected
        if any(keyword in prompt.lower() for keyword in cs_keywords):
            st.session_state.cs_mode = True
        
        # Handle the CS flow
        if st.session_state.cs_mode:
            # Get response from CS handler
            for response_chunk in get_response_with_rag(
                bedrock_client,
                runtime_client,
                prompt,
                phone_number=st.session_state.phone_number,
                dynamodb=dynamodb
            ):
                full_response += response_chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
            # Update state based on response
            if "what's the best phone number" in full_response.lower():
                st.session_state.phone_number = None
            elif sum(c.isdigit() for c in prompt) >= 10:
                st.session_state.phone_number = prompt
            
            # Reset CS mode if call is initiated
            if "sara will be calling you right now" in full_response.lower():
                st.session_state.cs_mode = False
                st.session_state.phone_number = None
        else:
            # Regular RAG response for non-CS interactions
            for response_chunk in get_response_with_rag(
                bedrock_client,
                runtime_client,
                prompt,
                dynamodb=dynamodb
            ):
                full_response += response_chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a reset button
if st.sidebar.button("Reset Chat"):
    st.session_state.messages = []
    st.session_state.phone_number = None
    st.session_state.cs_mode = False
    st.rerun()