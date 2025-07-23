# 🔬 AI Research Team System

An interactive Streamlit app that decomposes a research topic, performs detailed research using Google Gemini AI, and generates a professional summary report.

### 🌐 Live App: [https://research-agents.streamlit.app](https://research-agents.streamlit.app)

---

## 🚀 Features

- 🌐 **Google Gemini Integration**  
  Leverages the power of Google's Generative AI (`gemini-1.5-flash`) to:
  - Break a topic into 3–5 sub-topics
  - Research each sub-topic with detailed factual insights
  - Summarize all findings into a final research report

- 🧠 **AI Agent Architecture**
  - **DecomposerAgent** – Breaks down the topic into focused, researchable sub-topics
  - **ResearchAgent** – Conducts deep research and generates a paragraph for each sub-topic
  - **SummarizerAgent** – Synthesizes the findings into a cohesive, structured report

- 💻 **Streamlit Frontend**
  - Secure API key input
  - Progress tracking
  - Expandable sections for each sub-topic’s research
  - Downloadable final report

---

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Bhaumik-99/research_agents.git
   cd research_agents
   ```


2. **Make sure you have **Python 3.8+** installed, then install the required libraries:**

  ```bash
  pip install -r requirements.txt
  ```

---

## 📄 License

This project is licensed under the **MIT License** — you are free to use, modify, and distribute it with attribution.
