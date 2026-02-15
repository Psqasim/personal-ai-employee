# UI Components Reference

Essential Streamlit widgets and layout components for chatbot interfaces.

## Input Widgets

### Text Input

Single-line text input for names, settings, API keys, etc.

```python
name = st.text_input("Enter your name")
api_key = st.text_input("API Key", type="password")
model = st.text_input("Model name", value="gpt-4")
```

**Parameters:**
- `label` (str): Label displayed above the input
- `value` (str, optional): Default value
- `type` (str, optional): "default" or "password" for hidden input
- `placeholder` (str, optional): Placeholder text
- `disabled` (bool, optional): Disable the input
- `key` (str, optional): Unique key for the widget

### Text Area

Multi-line text input for longer content.

```python
system_prompt = st.text_area(
    "System prompt",
    value="You are a helpful assistant.",
    height=150
)
```

**Parameters:**
- `label` (str): Label displayed above the input
- `value` (str, optional): Default text
- `height` (int, optional): Height in pixels
- `placeholder` (str, optional): Placeholder text

### Number Input

Numeric input with increment/decrement buttons.

```python
temperature = st.number_input(
    "Temperature",
    min_value=0.0,
    max_value=2.0,
    value=0.7,
    step=0.1
)

max_tokens = st.number_input(
    "Max tokens",
    min_value=1,
    max_value=4000,
    value=2000,
    step=100
)
```

### Slider

Visual slider for numeric ranges.

```python
temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_tokens = st.slider("Max tokens", 100, 4000, 2000, 100)
```

### Select Box

Dropdown menu for single selection.

```python
model = st.selectbox(
    "Choose model",
    ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
)

tone = st.selectbox(
    "Response tone",
    ["Professional", "Casual", "Friendly", "Technical"]
)
```

**Parameters:**
- `label` (str): Label for the dropdown
- `options` (list): List of options
- `index` (int, optional): Default selection index
- `key` (str, optional): Unique key

### Multi-Select

Multiple selection dropdown.

```python
capabilities = st.multiselect(
    "Enable capabilities",
    ["Web search", "Code execution", "Image generation", "File analysis"],
    default=["Web search"]
)
```

### Checkbox

Boolean toggle for enabling/disabling features.

```python
enable_streaming = st.checkbox("Enable streaming", value=True)
save_history = st.checkbox("Save conversation history")
show_thinking = st.checkbox("Show reasoning process")
```

### Toggle

Modern toggle switch (alternative to checkbox).

```python
dark_mode = st.toggle("Dark mode")
auto_save = st.toggle("Auto-save conversations", value=True)
```

### Button

Trigger actions.

```python
if st.button("Clear conversation"):
    st.session_state.messages = []
    st.rerun()

if st.button("Export chat", type="primary"):
    export_conversation()

if st.button("Reset settings", type="secondary"):
    reset_to_defaults()
```

**Parameters:**
- `label` (str): Button text
- `type` (str, optional): "primary", "secondary", or "tertiary" for styling
- `disabled` (bool, optional): Disable the button
- `use_container_width` (bool, optional): Full width button

### File Uploader

Upload files for processing.

```python
uploaded_file = st.file_uploader(
    "Upload a document",
    type=["txt", "pdf", "docx"]
)

if uploaded_file:
    content = uploaded_file.read()
    # Process file content
```

**Parameters:**
- `label` (str): Label for the uploader
- `type` (list, optional): Allowed file extensions
- `accept_multiple_files` (bool, optional): Allow multiple files

### Color Picker

Select colors for theming.

```python
accent_color = st.color_picker("Accent color", "#00BFFF")
```

## Layout Components

### Columns

Side-by-side layout.

```python
col1, col2 = st.columns(2)
with col1:
    st.write("Left column")
    model = st.selectbox("Model", ["gpt-4", "claude"])
with col2:
    st.write("Right column")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)

# Unequal columns
col1, col2, col3 = st.columns([2, 1, 1])
```

**Use cases:**
- Settings panels with multiple inputs
- Action buttons side-by-side
- Multi-column layouts for configuration

### Sidebar

Persistent sidebar for settings and controls.

```python
with st.sidebar:
    st.title("Settings")

    model = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"])
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7)

    st.divider()

    if st.button("Clear history"):
        st.session_state.messages = []
        st.rerun()
```

**Alternative syntax:**
```python
st.sidebar.title("Settings")
st.sidebar.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"])
```

### Tabs

Organize content into tabs.

```python
tab1, tab2, tab3 = st.tabs(["Chat", "History", "Settings"])

with tab1:
    # Chat interface
    display_chat()

with tab2:
    # Conversation history
    display_history()

with tab3:
    # Settings panel
    display_settings()
```

### Expander

Collapsible sections.

```python
with st.expander("Advanced settings"):
    max_tokens = st.number_input("Max tokens", 100, 4000, 2000)
    top_p = st.slider("Top P", 0.0, 1.0, 1.0)
    frequency_penalty = st.slider("Frequency penalty", 0.0, 2.0, 0.0)

with st.expander("See conversation context"):
    st.json(st.session_state.messages)
```

### Container

Generic container for grouping elements.

```python
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
```

**Use cases:**
- Scrollable chat history
- Grouping related elements
- Dynamic content areas

## Display Elements

### Text and Markdown

```python
st.title("AI Chatbot")
st.header("Configuration")
st.subheader("Model Settings")
st.text("Plain text")
st.markdown("**Bold** and *italic*")
st.caption("Small caption text")
```

### Code

```python
code = '''
def hello():
    print("Hello, World!")
'''
st.code(code, language="python")
```

### Divider

Visual separator.

```python
st.divider()
```

### JSON

Display JSON data.

```python
st.json({"model": "gpt-4", "temperature": 0.7})
```

## Status Elements

### Success, Info, Warning, Error

```python
st.success("Message sent successfully!")
st.info("Using GPT-4 model")
st.warning("API key not configured")
st.error("Failed to connect to API")
```

### Toast

Temporary notification.

```python
st.toast("Settings saved!", icon="✅")
st.toast("Processing...", icon="⏳")
```

## Complete Sidebar Configuration Example

```python
import streamlit as st

with st.sidebar:
    st.title("⚙️ Configuration")

    # Model settings
    st.subheader("Model")
    model = st.selectbox(
        "Choose model",
        ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0
    )

    # Parameters
    st.subheader("Parameters")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.number_input("Max tokens", 100, 4000, 2000, 100)

    # Advanced settings
    with st.expander("Advanced"):
        top_p = st.slider("Top P", 0.0, 1.0, 1.0, 0.05)
        frequency_penalty = st.slider("Frequency penalty", 0.0, 2.0, 0.0, 0.1)

    # System prompt
    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "Enter system prompt",
        value="You are a helpful assistant.",
        height=100
    )

    # Actions
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("Export", use_container_width=True):
            # Export logic
            st.toast("Exported!", icon="✅")
```
