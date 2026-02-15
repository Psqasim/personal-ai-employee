# Session State Management

Complete guide to managing state in Streamlit applications for chatbots.

## What is Session State?

Streamlit reruns your entire script from top to bottom on every user interaction. Session State allows you to preserve variables across these reruns, essential for maintaining conversation history, user settings, and application state.

## Basic Usage

### Initializing Session State

Always initialize session state variables before using them:

```python
import streamlit as st

# Check if variable exists, if not initialize it
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "model_config" not in st.session_state:
    st.session_state.model_config = {
        "temperature": 0.7,
        "max_tokens": 2000
    }
```

### Reading from Session State

```python
# Access values
messages = st.session_state.messages
temperature = st.session_state.model_config["temperature"]

# Check if exists
if "api_key" in st.session_state:
    api_key = st.session_state.api_key
```

### Writing to Session State

```python
# Direct assignment
st.session_state.messages.append({"role": "user", "content": "Hello"})
st.session_state.user_name = "Alice"

# Update dictionary
st.session_state.model_config["temperature"] = 0.9
```

## Chat Application Patterns

### Pattern 1: Simple Message History

```python
import streamlit as st

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Accept new message
if prompt := st.chat_input("Your message"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    response = generate_response(prompt)

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Rerun to display new messages
    st.rerun()
```

### Pattern 2: Multi-Stage Workflow

For applications with validation, editing, or approval steps:

```python
import streamlit as st

# Initialize workflow state
if "stage" not in st.session_state:
    st.session_state.stage = "input"  # input, processing, validation, complete
    st.session_state.messages = []
    st.session_state.pending_response = None

# Stage 1: User input
if st.session_state.stage == "input":
    if prompt := st.chat_input("Ask something"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.stage = "processing"
        st.rerun()

# Stage 2: Processing
elif st.session_state.stage == "processing":
    with st.spinner("Thinking..."):
        response = generate_response(st.session_state.messages[-1]["content"])
        st.session_state.pending_response = response
        st.session_state.stage = "validation"
        st.rerun()

# Stage 3: Validation
elif st.session_state.stage == "validation":
    st.chat_input("Review the response", disabled=True)
    with st.chat_message("assistant"):
        st.write(st.session_state.pending_response)

        col1, col2 = st.columns(2)
        if col1.button("Accept"):
            st.session_state.messages.append({
                "role": "assistant",
                "content": st.session_state.pending_response
            })
            st.session_state.pending_response = None
            st.session_state.stage = "input"
            st.rerun()

        if col2.button("Regenerate"):
            st.session_state.stage = "processing"
            st.rerun()
```

### Pattern 3: Conversation with Metadata

Store additional metadata alongside messages:

```python
import streamlit as st
from datetime import datetime

if "messages" not in st.session_state:
    st.session_state.messages = []

# Message structure with metadata
message = {
    "role": "assistant",
    "content": "Hello! How can I help?",
    "timestamp": datetime.now().isoformat(),
    "model": "gpt-4",
    "tokens": 150,
    "feedback": None  # Will store user feedback
}

st.session_state.messages.append(message)
```

### Pattern 4: Separate Conversations

Manage multiple conversation threads:

```python
import streamlit as st

# Initialize conversations
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    st.session_state.current_conversation = "default"

if "conversation_counter" not in st.session_state:
    st.session_state.conversation_counter = 0

# Create new conversation
def new_conversation():
    conv_id = f"conv_{st.session_state.conversation_counter}"
    st.session_state.conversations[conv_id] = {
        "messages": [],
        "title": f"Conversation {st.session_state.conversation_counter + 1}",
        "created_at": datetime.now()
    }
    st.session_state.current_conversation = conv_id
    st.session_state.conversation_counter += 1

# Get current messages
current = st.session_state.current_conversation
messages = st.session_state.conversations[current]["messages"]

# Switch conversations
with st.sidebar:
    st.selectbox(
        "Select conversation",
        options=list(st.session_state.conversations.keys()),
        format_func=lambda x: st.session_state.conversations[x]["title"],
        key="current_conversation"
    )
    if st.button("New conversation"):
        new_conversation()
        st.rerun()
```

## Configuration Management

### Pattern: Persistent Settings

```python
import streamlit as st

# Initialize settings
if "settings" not in st.session_state:
    st.session_state.settings = {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "system_prompt": "You are a helpful assistant.",
        "streaming": True
    }

# Settings UI in sidebar
with st.sidebar:
    st.title("Settings")

    # Use session state in widgets with callback
    model = st.selectbox(
        "Model",
        ["gpt-4", "gpt-3.5-turbo", "claude-3"],
        index=["gpt-4", "gpt-3.5-turbo", "claude-3"].index(
            st.session_state.settings["model"]
        ),
        key="model_select"
    )
    st.session_state.settings["model"] = model

    temperature = st.slider(
        "Temperature",
        0.0, 2.0,
        st.session_state.settings["temperature"],
        0.1
    )
    st.session_state.settings["temperature"] = temperature

    # Reset to defaults
    if st.button("Reset to defaults"):
        st.session_state.settings = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "system_prompt": "You are a helpful assistant.",
            "streaming": True
        }
        st.rerun()
```

## Widget Callbacks

Use callbacks to update session state when widgets change:

```python
import streamlit as st

def update_temperature():
    """Callback when temperature slider changes"""
    st.session_state.config["temperature"] = st.session_state.temp_slider
    st.toast(f"Temperature updated to {st.session_state.temp_slider}")

def clear_history():
    """Callback when clear button is clicked"""
    st.session_state.messages = []
    st.toast("Conversation cleared")

# Initialize
if "config" not in st.session_state:
    st.session_state.config = {"temperature": 0.7}

if "messages" not in st.session_state:
    st.session_state.messages = []

# Widget with callback
st.slider(
    "Temperature",
    0.0, 2.0, 0.7, 0.1,
    key="temp_slider",
    on_change=update_temperature
)

st.button("Clear chat", on_click=clear_history)
```

## Common Pitfalls and Solutions

### Pitfall 1: Not Initializing Before Use

```python
# ❌ BAD - Will error on first run
st.session_state.messages.append(message)

# ✅ GOOD - Check first
if "messages" not in st.session_state:
    st.session_state.messages = []
st.session_state.messages.append(message)
```

### Pitfall 2: Modifying Mutable Objects

```python
# ❌ POTENTIALLY PROBLEMATIC
messages = st.session_state.messages
messages.append(new_message)  # Modifies original, might not trigger rerun

# ✅ SAFER
st.session_state.messages = st.session_state.messages + [new_message]
# or
st.session_state.messages.append(new_message)
st.rerun()  # Explicit rerun
```

### Pitfall 3: Infinite Rerun Loops

```python
# ❌ BAD - Creates infinite loop
if prompt := st.chat_input("Message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()  # This causes the chat_input to be evaluated again

# ✅ GOOD - Only rerun when necessary
if prompt := st.chat_input("Message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Generate response
    response = generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()  # Rerun to display both messages
```

### Pitfall 4: Widget Key Conflicts

```python
# ❌ BAD - Same key used multiple times
st.button("Action", key="btn")
st.button("Another action", key="btn")  # Error!

# ✅ GOOD - Unique keys
st.button("Action", key="btn_1")
st.button("Another action", key="btn_2")
```

## Debugging Session State

View current session state for debugging:

```python
import streamlit as st

# Add debug expander in development
if st.checkbox("Show debug info"):
    st.subheader("Session State")
    st.json(dict(st.session_state))

# Or use expander
with st.expander("Debug: Session State"):
    for key, value in st.session_state.items():
        st.write(f"**{key}:**", value)
```

## Advanced: Custom Session State Manager

For complex applications, create a state manager:

```python
import streamlit as st
from typing import Any, Dict, List

class ChatStateManager:
    """Manages chat application state"""

    @staticmethod
    def initialize():
        """Initialize all required session state variables"""
        if "initialized" not in st.session_state:
            st.session_state.messages = []
            st.session_state.settings = {
                "model": "gpt-4",
                "temperature": 0.7
            }
            st.session_state.current_stage = "input"
            st.session_state.initialized = True

    @staticmethod
    def add_message(role: str, content: str, **metadata):
        """Add a message to history"""
        message = {
            "role": role,
            "content": content,
            **metadata
        }
        st.session_state.messages.append(message)

    @staticmethod
    def clear_messages():
        """Clear message history"""
        st.session_state.messages = []

    @staticmethod
    def get_messages() -> List[Dict]:
        """Get all messages"""
        return st.session_state.messages

    @staticmethod
    def update_setting(key: str, value: Any):
        """Update a setting"""
        st.session_state.settings[key] = value

    @staticmethod
    def get_setting(key: str, default=None) -> Any:
        """Get a setting value"""
        return st.session_state.settings.get(key, default)

# Usage
ChatStateManager.initialize()
ChatStateManager.add_message("user", "Hello")
messages = ChatStateManager.get_messages()
```
