# App Configuration and Styling

Guide to configuring Streamlit apps with page settings, themes, and styling.

## Page Configuration

Set page metadata and layout with `st.set_page_config()`. **MUST be called before any other Streamlit command.**

### Basic Configuration

```python
import streamlit as st

st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rest of your app...
```

### All Parameters

```python
st.set_page_config(
    page_title="AI Chatbot",           # Browser tab title
    page_icon="🤖",                     # Browser tab icon (emoji or image path)
    layout="wide",                      # "centered" or "wide"
    initial_sidebar_state="expanded",   # "auto", "expanded", "collapsed"
    menu_items={
        'Get Help': 'https://docs.example.com',
        'Report a bug': 'https://github.com/user/repo/issues',
        'About': 'My AI Chatbot v1.0'
    }
)
```

**Parameters:**
- `page_title`: Text shown in browser tab (default: "Streamlit")
- `page_icon`: Emoji or path to icon image
- `layout`: "centered" (default) or "wide" for full-width layout
- `initial_sidebar_state`: "auto", "expanded", or "collapsed"
- `menu_items`: Dictionary with optional 'Get Help', 'Report a bug', 'About' links

### Layout Options

**Centered (default):**
- Content is centered with max-width
- Good for focused, single-column apps

```python
st.set_page_config(layout="centered")
```

**Wide:**
- Content uses full browser width
- Good for dashboards and data-heavy apps

```python
st.set_page_config(layout="wide")
```

## Custom Styling with CSS

### Method 1: st.markdown with HTML/CSS

```python
import streamlit as st

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)
```

### Method 2: External CSS File

Create `.streamlit/config.toml` in your project root:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

### Common Styling Examples

**Hide Streamlit Branding:**
```python
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
```

**Custom Chat Message Styling:**
```python
st.markdown("""
    <style>
    .stChatMessage {
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    .stChatMessage[data-testid="user-message"] {
        background-color: #2b5278;
    }
    </style>
""", unsafe_allow_html=True)
```

**Custom Sidebar:**
```python
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }
    [data-testid="stSidebar"] h1 {
        color: #FF4B4B;
    }
    </style>
""", unsafe_allow_html=True)
```

**Custom Buttons:**
```python
st.markdown("""
    <style>
    .stButton > button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 20px;
        padding: 10px 24px;
        border: none;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #FF6B6B;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)
```

## Theme Configuration

### config.toml Theme Settings

Create `.streamlit/config.toml`:

```toml
[theme]
# Primary accent color
primaryColor = "#FF4B4B"

# Background color for the main content area
backgroundColor = "#FFFFFF"

# Background color used for the sidebar and most interactive widgets
secondaryBackgroundColor = "#F0F2F6"

# Color used for almost all text
textColor = "#262730"

# Font family for all text
# Options: "sans serif", "serif", "monospace"
font = "sans serif"
```

### Dark Theme Example

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

### Light Theme Example

```toml
[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#1E1E1E"
font = "sans serif"
```

## Caching and Performance

### st.cache_data

Cache data loading operations:

```python
import streamlit as st
import pandas as pd

@st.cache_data
def load_model():
    """Load and cache ML model"""
    # Expensive model loading
    return model

@st.cache_data
def fetch_data(api_key):
    """Fetch and cache API data"""
    # API call
    return data

# Usage
model = load_model()
data = fetch_data(st.session_state.api_key)
```

**Use for:**
- Loading data from files
- API calls
- Database queries
- Data transformations

### st.cache_resource

Cache resources that should be shared across users:

```python
import streamlit as st
from openai import OpenAI

@st.cache_resource
def get_openai_client():
    """Create and cache OpenAI client"""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Usage
client = get_openai_client()
```

**Use for:**
- ML models
- Database connections
- API clients
- Heavy objects that should persist

### Clear Cache

```python
import streamlit as st

if st.button("Clear cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
```

## Secrets Management

### Using st.secrets

Create `.streamlit/secrets.toml`:

```toml
# API keys
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

# Database credentials
[database]
host = "localhost"
port = 5432
username = "user"
password = "pass"

# Custom configuration
[app]
model = "gpt-4"
max_tokens = 2000
```

### Accessing Secrets

```python
import streamlit as st

# Simple secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Nested secrets
db_host = st.secrets["database"]["host"]
db_port = st.secrets["database"]["port"]

# With defaults
model = st.secrets.get("app", {}).get("model", "gpt-3.5-turbo")

# Check if exists
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
```

### Production Secrets (Streamlit Cloud)

For deployed apps, add secrets in the Streamlit Cloud dashboard:
1. Go to app settings
2. Navigate to "Secrets" section
3. Paste secrets in TOML format
4. Save and redeploy

## Status and Loading Indicators

### Spinner

```python
import streamlit as st
import time

with st.spinner("Thinking..."):
    time.sleep(2)
    response = generate_response(prompt)
```

### Progress Bar

```python
import streamlit as st
import time

progress_bar = st.progress(0)
for i in range(100):
    time.sleep(0.01)
    progress_bar.progress(i + 1)
```

### Status Container

```python
import streamlit as st
import time

with st.status("Processing your request...", expanded=True) as status:
    st.write("Loading model...")
    time.sleep(1)

    st.write("Generating response...")
    time.sleep(2)

    st.write("Formatting output...")
    time.sleep(1)

    status.update(label="Complete!", state="complete", expanded=False)
```

**States:**
- "running" (default): Shows spinner
- "complete": Shows checkmark
- "error": Shows error icon

## Multi-Page Apps

### File Structure

```
my_app/
├── app.py                 # Main entry point
├── pages/
│   ├── 1_Chat.py
│   ├── 2_History.py
│   └── 3_Settings.py
└── .streamlit/
    └── config.toml
```

### Main App (app.py)

```python
import streamlit as st

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Assistant")
st.write("Welcome! Use the sidebar to navigate.")
```

### Page Example (pages/1_Chat.py)

```python
import streamlit as st

st.title("💬 Chat")

# Chat implementation...
```

### st.Page and st.navigation (New Method)

```python
import streamlit as st

# Define pages
chat_page = st.Page("chat.py", title="Chat", icon="💬")
history_page = st.Page("history.py", title="History", icon="📜")
settings_page = st.Page("settings.py", title="Settings", icon="⚙️")

# Create navigation
pg = st.navigation([chat_page, history_page, settings_page])

# Configure app
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖"
)

# Run selected page
pg.run()
```

## Environment Variables

### Using python-dotenv

```python
import streamlit as st
from dotenv import load_dotenv
import os

# Load .env file (in development)
load_dotenv()

# Access environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Or use st.secrets in production
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = os.getenv("OPENAI_API_KEY")
```

## Complete Configuration Example

```python
import streamlit as st
from openai import OpenAI

# ============================================================================
# PAGE CONFIGURATION (must be first)
# ============================================================================
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.example.com',
        'Report a bug': 'https://github.com/user/repo/issues',
        'About': 'AI Chatbot powered by GPT-4'
    }
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom chat messages */
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
    """Initialize OpenAI client (cached)"""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

client = get_openai_client()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "settings" not in st.session_state:
    st.session_state.settings = {
        "model": "gpt-4",
        "temperature": 0.7
    }

# Rest of app...
```
