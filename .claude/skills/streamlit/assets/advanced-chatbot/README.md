# Advanced Streamlit Chatbot

Production-ready chatbot with OpenAI integration and advanced features.

## Features

- ✅ OpenAI GPT-4/3.5 integration
- ✅ Streaming responses with typewriter effect
- ✅ Configurable model parameters (temperature, max tokens)
- ✅ Custom system prompts
- ✅ Message feedback collection (thumbs up/down)
- ✅ Conversation export to JSON
- ✅ Dark theme with custom styling
- ✅ Responsive sidebar configuration

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure API key:**

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```

Or copy the example file:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Then edit it with your API key.

3. **Run the app:**
```bash
streamlit run app.py
```

4. **Open your browser:**
Navigate to `http://localhost:8501`

## Configuration

### Model Settings

Adjust in the sidebar:
- **Model**: Choose between GPT-4, GPT-4 Turbo, or GPT-3.5 Turbo
- **Temperature**: Control randomness (0.0 = focused, 2.0 = creative)
- **Max Tokens**: Limit response length
- **Streaming**: Enable/disable typewriter effect

### System Prompt

Customize the AI's behavior and personality through the system prompt in the sidebar.

### Theme

Modify `.streamlit/config.toml` to change colors and appearance.

## Customization

### Adding Other LLM Providers

Replace the `get_openai_response()` function with your preferred provider:

```python
# For Anthropic Claude:
from anthropic import Anthropic
client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# For local models (Ollama, etc.):
# Implement custom API client
```

### Extending Features

- Add conversation history persistence (database, file storage)
- Implement user authentication
- Add file upload for document Q&A
- Create multi-agent conversations
- Add RAG (Retrieval Augmented Generation)

## Production Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in app settings
4. Deploy

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Environment Variables

For production, use environment variables instead of secrets.toml:

```python
import os
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
```

## Troubleshooting

**API Key Error:**
- Ensure `.streamlit/secrets.toml` exists with valid API key
- Check file is in the correct location (same directory as app.py)

**Import Error:**
- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

**Streaming Not Working:**
- Check "Enable streaming" toggle in sidebar
- Verify OpenAI library version (should be 1.0.0+)

## License

MIT License - feel free to use and modify for your projects.
