import streamlit as st
from bedrock_utils import init_bedrock, get_response_with_rag
from dynamo_utils import init_dynamodb

# Initialize Bedrock clients
bedrock_client, runtime_client = init_bedrock()
dynamodb = init_dynamodb()

# Set page config with custom theme
st.set_page_config(
    page_title="Rivertown Ball Company",
    page_icon="🟤",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #fef3c7;
        background-image: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin: 10px 0 !important;
    }
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.8);
    }
    h1 {
        color: #92400e !important;
        text-align: center;
        padding: 20px 0;
        font-family: 'Arial', sans-serif;
    }
    .stButton > button {
        background-color: #f59e0b;
        color: white;
        border-radius: 10px;
    }
    .stButton > button:hover {
        background-color: #d97706;
    }
    </style>
    """, unsafe_allow_html=True)

# Header with logo and title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🟤 Rivertown Ball Company")
    st.markdown("""
        <p style='text-align: center; color: #92400e; margin-bottom: 30px;'>
        Crafting Premium Wooden Balls Since 1923
        </p>
    """, unsafe_allow_html=True)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Welcome to Rivertown Ball Company! How can I help you today?"
    })
if "phone_number" not in st.session_state:
    st.session_state.phone_number = None
if "cs_mode" not in st.session_state:
    st.session_state.cs_mode = False

# Create a container for chat messages
chat_container = st.container()

# Display chat messages from history on app rerun
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask about our wooden balls..."):
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

# Sidebar with reset button and additional info
with st.sidebar:
    st.markdown("### Chat Controls")
    if st.button("Reset Chat", key="reset"):
        st.session_state.messages = []
        st.session_state.phone_number = None
        st.session_state.cs_mode = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
        ### About Us
        Rivertown Ball Company has been crafting premium wooden balls 
        for over a century. Our commitment to quality and craftsmanship 
        makes us the leading choice for wooden ball products.
    """)