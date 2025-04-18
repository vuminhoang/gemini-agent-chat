# gemini-agent-chat

Create a Gemini agent chat!

## 🚀 Getting Started

### 1. Clone repository

```bash
git clone https://github.com/your-username/gemini-agent-chat.git
cd gemini-agent-chat/services/assistant
```

### 2. Install libs
```bash
pip install -r requirements.txt
```

### 3. Set up API Key
- Get your Gemini API Key on Google Studio.
- Create a dev.toml file based on the dev.toml.example template.Fill in the required fields such as API keys, endpoints, etc.

### 4. Run the assistant service
- In folfer asssistant:
```bash
uvicorn webhook:app --reload --host 0.0.0.0 --port 8000
```
After that, click on http://localhost:8000/docs, you will see the Swagger UI.

Click on Chat -> Try it out -> Enter the request body!





