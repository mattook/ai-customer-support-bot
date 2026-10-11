# MY COPY
# Production-Grade RAG AI Customer Support Bot for Slack

A high-fidelity, enterprise-ready RAG (Retrieval-Augmented Generation) customer support system built in Python. This bot utilizes a custom document crawler, semantic chunking, `pgvector` for vector storage, OpenAI for embeddings, Anthropic Claude-3.5-Haiku for generation, and Slack Bolt for real-time team communication.

It prioritizes strict probabilistic guardrails, low-latency asynchronous processing, and robust reliability over low-code shortcuts.

---

## Architecture & Tech Stack

*   **Framework:** Flask (running on Port 8000)
*   **Database & Vector Search:** PostgreSQL with the `pgvector` extension
*   **Embeddings:** OpenAI `text-embedding-3-small`
*   **LLM Inference:** Anthropic `claude-3-5-haiku-20241022`
*   **Slack Integration:** Slack Bolt (`SlackRequestHandler`) with asynchronous response handling (`process_before_response=True`)

---

## Features

*   **Recursive Documentation Crawler:** Scrapes root-level documentation (`/docs/`) with clean HTML processing and semantic chunking.
*   **No-Hallucination Guardrails:** Implements TypeSafe Jev confidence gating (target confidence: 0.6–0.7) to restrict responses strictly to verified context.
*   **Webhook Optimization:** Bypasses Slack's strict 3-second timeout rule during heavy LLM/RAG inference calls using non-blocking thread handling.

---

## Prerequisites

*   Python 3.10+
*   PostgreSQL installed locally or hosted, with `pgvector` enabled:
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
*   An active Slack App with a Bot Token and Event Subscriptions configured.

---

## Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Set Up a Virtual Environment
```python
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory based on the provided template (`.env.example`):

```env
FLASK_RUN_PORT=8000
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key
DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name
```

---

## Running the Application

### 0. Populate the vector database for the first time
```bash
python3.11 ingest.py
```

### 1. Start the Flask Server
```bash
python3.11 main.py
```
*(The server will start locally on port `8000`)*

### 2. Open an Ngrok Tunnel
In a separate terminal window, expose your local server to the internet via ngrok:
```bash
ngrok http 8000
```
Copy your active HTTPS forwarding URL (e.g., `https://xxxx-xxxx.ngrok-free.app`).

### 3. Configure Slack App Event Subscriptions
1. Go to your [Slack App Dashboard](https://api.slack.com/apps).
2. **Important:** Ensure **Socket Mode** is **DISABLED** under Basic Information (this project uses HTTP Webhooks).
3. Navigate to **Event Subscriptions** and toggle **Enable Events** to **ON**.
4. Set your Request URL to: `https://your-url.ngrok-free.app/slack/events`
5. Subscribe to the bot event: `app_mention`.
6. Go to **OAuth & Permissions** and verify you have the `app_mentions:read` and `chat:write` bot scopes.
7. Click **Reinstall to Workspace** if prompted.

---

## Usage

1. Invite your bot to a public Slack channel:
   ```text
   /invite @YourBotName
   ```
2. Tag your bot with a customer support question:
   ```text
   @YourBotName how do I reset my API key?
   ```
3. The system will asynchronously fetch relevant documentation snippets from `pgvector`, evaluate confidence via the Jev gate, query Claude-3.5-Haiku, and reply directly inside the thread.
