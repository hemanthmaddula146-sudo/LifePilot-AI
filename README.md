# 🚀 LifePilot-AI
### AI-Powered Personal Productivity Assistant

LifePilot-AI is an AI-powered personal productivity and study assistant built with Python, Google Gemini, and the Model Context Protocol (MCP).

It helps users manage tasks, calculate study time, and receive AI-powered study guidance through an MCP server.
# LifePilot-AI 🚀

### 🤖 Your Personal AI Productivity Assistant

🌐 **Live Demo:** https://lifepilot-ai-hemanth.streamlit.app

💻 **GitHub Repository:** https://github.com/hemanthmaddula146-sudo/LifePilot-AI

---

## ✨ Features

- 🤖 **AI Study Assistant:** Get study guidance and practical explanations using Google Gemini.
- ✅ **Task Management:** Add, list, complete, and delete tasks.
- ⏱️ **Study-Time Calculator:** Calculate study time across multiple subjects.
- 🔌 **MCP Integration:** Access productivity tools through the Model Context Protocol.
- 🗄️ **SQLite Database:** Store tasks locally.
- 🔐 **Environment Configuration:** Keep API keys out of source code.
- 🧪 **Testing:** Test task management, Gemini integration, and MCP tools.

## 🛠️ Technology Stack

- Python
- Google Gemini API
- Google Gen AI SDK
- Model Context Protocol (MCP)
- Streamable HTTP
- SQLite
- python-dotenv
- Git and GitHub

## 📁 Project Structure

```text
LifePilot-AI/
├── server.py
├── test_gemini.py
├── test_mcp.py
├── test_tasks.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Prerequisites

- Python 3.11 or later
- Git
- Google Gemini API key

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/hemanthmaddula146-sudo/LifePilot-AI.git
cd LifePilot-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Configure your API key

Copy `.env.example` to `.env` and add your Gemini API key to `.env`.

Never upload your `.env` file or expose your API key publicly.

### 6. Start the MCP server

```bash
python server.py
```

The local MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Keep the server running while using the MCP tools.

## 🧪 Testing

Run the available tests individually:

```bash
python test_tasks.py
python test_gemini.py
python test_mcp.py
```

Make sure the MCP server is running before executing `test_mcp.py`.

## 🔒 Security

- Store API keys in environment variables or an untracked `.env` file.
- Never commit API keys or other secrets to GitHub.
- The SQLite database is intended for local development.

## 🗺️ Future Improvements

- [ ] Build a user-friendly web interface.
- [ ] Improve task scheduling and productivity workflows.
- [ ] Add configurable study plans.
- [ ] Expand automated test coverage.
- [ ] Prepare a secure deployment configuration.

## 👨‍💻 Author

**Hemanth Maddula**

GitHub: [hemanthmaddula146-sudo](https://github.com/hemanthmaddula146-sudo)

---

Built with Python, Gemini AI, and MCP.
