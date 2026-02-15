# Chat Components Reference

Complete guide to Streamlit's chat interface components for building AI chatbots.

## st.chat_input

Display a chat input widget for user messages.

**Syntax:**
```python
prompt = st.chat_input(placeholder="Say something")
if prompt:
    # Process the user's message
    st.write(f"User said: {prompt}")
```

**Parameters:**
- `placeholder` (str, optional): Placeholder text shown in the input field

**Returns:**
- `str` or `None`: The text entered by user, or None if nothing entered

**Best Practices:**
- Use the walrus operator (`:=`) for concise code: `if prompt := st.chat_input("Say something"):`
- Always check if prompt exists before processing
- Disable during validation/processing: `st.chat_input("Thinking...", disabled=True)`

## st.chat_message

Create a chat message container for displaying messages with role-based styling.

**Syntax:**
```python
with st.chat_message("user"):
    st.write("Hello!")

with st.chat_message("assistant"):
    st.write("Hi there! How can I help?")
```

**Parameters:**
- `name` (str): Role of the message sender - "user", "assistant", or "ai"

**Features:**
- Automatically styles messages based on role
- User messages align right, assistant messages align left
- Can contain any Streamlit elements (text, images, charts, etc.)

**Example - Complete Chat Display:**
```python
# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
```

## st.write_stream

Display streaming text with typewriter effect - essential for LLM responses.

**Syntax:**
```python
response = st.write_stream(my_generator)
# or
response = st.write_stream(my_llm_stream)
```

**Parameters:**
- `stream_data` (generator): A generator or stream that yields text chunks

**Returns:**
- `str`: The complete accumulated text from the stream

**Example - Basic Generator:**
```python
def response_generator():
    response = "Hello! How can I help you today?"
    for char in response:
        yield char
        time.sleep(0.02)

with st.chat_message("assistant"):
    response = st.write_stream(response_generator())
```

**Example - OpenAI Stream:**
```python
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def openai_stream(prompt):
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

with st.chat_message("assistant"):
    response = st.write_stream(openai_stream(prompt))
```

**Key Points:**
- Returns the complete text, allowing you to save it to session state
- Creates engaging UX by showing text appear character-by-character
- Works with any generator function or streaming API

## st.feedback

Add feedback collection to chat messages (thumbs up/down, stars, faces).

**Syntax:**
```python
st.feedback("thumbs")
st.feedback("stars")
st.feedback("faces")
```

**Parameters:**
- `options` (str): Type of feedback - "thumbs", "stars", or "faces"
- `key` (str, optional): Unique key for the widget
- `disabled` (bool, optional): Disable after feedback given
- `on_change` (callable, optional): Callback function when feedback changes

**Example - Feedback with Storage:**
```python
def save_feedback(index):
    st.session_state.messages[index]["feedback"] = st.session_state[f"feedback_{index}"]

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            feedback = message.get("feedback", None)
            st.feedback(
                "thumbs",
                key=f"feedback_{i}",
                disabled=feedback is not None,
                on_change=save_feedback,
                args=[i]
            )
```

## Complete Chat Application Pattern

**Basic Structure:**
```python
import streamlit as st

# 1. Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 3. Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(prompt))
        st.session_state.messages.append({"role": "assistant", "content": response})
```

## Multi-Stage Chat (Validation, Editing)

For advanced workflows with validation and editing:

```python
if "stage" not in st.session_state:
    st.session_state.stage = "user"
    st.session_state.messages = []
    st.session_state.pending = None

# Stage 1: User input
if st.session_state.stage == "user":
    if prompt := st.chat_input("Ask something"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            response = st.write_stream(generate_response(prompt))
            st.session_state.pending = response
            st.session_state.stage = "validate"
            st.rerun()

# Stage 2: Validate response
elif st.session_state.stage == "validate":
    st.chat_input("Accept or edit the response above.", disabled=True)
    with st.chat_message("assistant"):
        st.write(st.session_state.pending)
        cols = st.columns(2)
        if cols[0].button("Accept"):
            st.session_state.messages.append(
                {"role": "assistant", "content": st.session_state.pending}
            )
            st.session_state.pending = None
            st.session_state.stage = "user"
            st.rerun()
        if cols[1].button("Regenerate"):
            st.session_state.stage = "user"
            st.rerun()
```
