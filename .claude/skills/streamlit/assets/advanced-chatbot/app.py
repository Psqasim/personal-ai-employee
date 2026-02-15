"""
Advanced Streamlit Chatbot with OpenAI Integration

A production-ready chatbot with:
- OpenAI GPT integration
- Configurable model parameters
- System prompts
- Conversation export
- Message feedback

Setup:
1. Create .streamlit/secrets.toml with your OpenAI API key
2. Install requirements: pip install -r requirements.txt
3. Run: streamlit run app.py
"""

import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom chat message styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# CACHED RESOURCES
# ============================================================================

@st.cache_resource
def get_openai_client():
    """Initialize and cache OpenAI client"""
    try:
        return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except KeyError:
        st.error("⚠️ OpenAI API key not found in secrets. Please configure .streamlit/secrets.toml")
        st.stop()

client = get_openai_client()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "settings" not in st.session_state:
    st.session_state.settings = {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "system_prompt": "You are a helpful AI assistant.",
        "streaming": True
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_openai_response(messages, settings):
    """
    Get response from OpenAI API with streaming support.

    Args:
        messages: List of conversation messages
        settings: Dictionary of model settings

    Yields:
        str: Response chunks for streaming
    """
    # Prepare messages with system prompt
    api_messages = [
        {"role": "system", "content": settings["system_prompt"]}
    ] + messages

    # Create streaming completion
    stream = client.chat.completions.create(
        model=settings["model"],
        messages=api_messages,
        temperature=settings["temperature"],
        max_tokens=settings["max_tokens"],
        stream=settings["streaming"]
    )

    # Yield chunks
    if settings["streaming"]:
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    else:
        # Non-streaming response
        yield stream.choices[0].message.content

def save_feedback(index):
    """Save user feedback for a message"""
    st.session_state.messages[index]["feedback"] = st.session_state[f"feedback_{index}"]

def export_conversation():
    """Export conversation to JSON"""
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "settings": st.session_state.settings,
        "messages": st.session_state.messages
    }
    return json.dumps(export_data, indent=2)

# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    st.title("⚙️ Configuration")

    # Model settings
    st.subheader("Model Settings")

    model = st.selectbox(
        "Model",
        ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"].index(st.session_state.settings["model"])
    )
    st.session_state.settings["model"] = model

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.settings["temperature"],
        step=0.1,
        help="Higher values make output more random, lower values more focused"
    )
    st.session_state.settings["temperature"] = temperature

    max_tokens = st.number_input(
        "Max tokens",
        min_value=100,
        max_value=4000,
        value=st.session_state.settings["max_tokens"],
        step=100,
        help="Maximum length of the response"
    )
    st.session_state.settings["max_tokens"] = max_tokens

    streaming = st.toggle(
        "Enable streaming",
        value=st.session_state.settings["streaming"],
        help="Show response as it's generated"
    )
    st.session_state.settings["streaming"] = streaming

    # System prompt
    st.divider()
    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "Customize the AI's behavior",
        value=st.session_state.settings["system_prompt"],
        height=100,
        help="Instructions that guide the AI's responses"
    )
    st.session_state.settings["system_prompt"] = system_prompt

    # Actions
    st.divider()
    st.subheader("Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear", use_container_width=True, help="Clear conversation history"):
            st.session_state.messages = []
            st.rerun()

    with col2:
        conversation_json = export_conversation()
        st.download_button(
            label="💾 Export",
            data=conversation_json,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            help="Export conversation to JSON"
        )

    # Stats
    st.divider()
    st.caption(f"**Messages:** {len(st.session_state.messages)}")
    st.caption(f"**Model:** {st.session_state.settings['model']}")

# ============================================================================
# MAIN APP - CHAT INTERFACE
# ============================================================================

st.title("🤖 AI Chatbot")
st.caption("Powered by OpenAI GPT")

# Display chat history with feedback
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

        # Add feedback widget for assistant messages
        if message["role"] == "assistant":
            feedback = message.get("feedback", None)
            st.session_state[f"feedback_{i}"] = feedback

            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                disabled=feedback is not None,
                on_change=save_feedback,
                args=[i]
            )

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate and display assistant response
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = st.write_stream(
                    get_openai_response(
                        st.session_state.messages,
                        st.session_state.settings
                    )
                )

            # Add feedback widget
            st.feedback(
                "thumbs",
                key=f"feedback_{len(st.session_state.messages)}",
                on_change=save_feedback,
                args=[len(st.session_state.messages)]
            )

            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "feedback": None
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your API key and try again.")
