# Real-Time AI Research System with WebSockets
# Install: pip install fastapi uvicorn websockets langchain langchain-openai langchain-community asyncio

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeResearchAgent:
    def __init__(self, name: str, role: str, tools: List[Tool], llm: ChatOpenAI):
        self.name = name
        self.role = role
        self.tools = tools
        self.llm = llm
        self.agent = self._create_agent()
    
    def _create_agent(self):
        system_message = f"""You are {self.name}, a specialized research agent.
        Role: {self.role}
        
        Provide concise, accurate research findings with clear sources.
        Focus on actionable insights and current information.
        Keep responses under 500 words for real-time delivery."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=False)
    
    async def research_async(self, query: str, websocket: WebSocket, agent_id: str) -> str:
        """Perform research and send real-time updates via WebSocket"""
        try:
            # Notify start
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "researching",
                "message": f"{self.name} is researching..."
            }))
            
            # Perform research (this is the actual API call)
            result = await asyncio.to_thread(
                self.agent.invoke, 
                {"input": query}
            )
            
            # Send result in real-time
            await websocket.send_text(json.dumps({
                "type": "research_result",
                "agent_id": agent_id,
                "agent_name": self.name,
                "result": result["output"]
            }))
            
            # Notify completion
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "completed",
                "message": f"{self.name} completed research"
            }))
            
            return result["output"]
            
        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            await websocket.send_text(json.dumps({
                "type": "agent_error",
                "agent_id": agent_id,
                "error": error_msg
            }))
            return error_msg

class RealTimeResearchTeam:
    def __init__(self):
        self.llm = ChatOpenAI(
        temperature=0.1,
        model="gpt-3.5-turbo",
        openai_api_key=''  # <- Injected from .env
    )
        self.agents = self._create_agents()
        self.active_sessions: Dict[str, Dict] = {}
    
    def _create_agents(self):
        # Create tools
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        try:
            tavily_search = TavilySearchResults(max_results=3)
        except:
            tavily_search = Tool(
                name="web_search",
                description="Search the web for information",
                func=lambda x: "Configure Tavily API key for web search"
            )
        
        # Create agents
        agents = {
            "researcher": RealTimeResearchAgent(
                name="Primary Researcher",
                role="Gather comprehensive background information",
                tools=[wikipedia, tavily_search],
                llm=self.llm
            ),
            "analyst": RealTimeResearchAgent(
                name="Data Analyst", 
                role="Analyze trends and statistics",
                tools=[tavily_search],
                llm=self.llm
            ),
            "news_tracker": RealTimeResearchAgent(
                name="News Tracker",
                role="Find recent developments and news",
                tools=[tavily_search],
                llm=self.llm
            ),
            "synthesizer": RealTimeResearchAgent(
                name="Information Synthesizer",
                role="Combine and synthesize all findings",
                tools=[],
                llm=self.llm
            )
        }
        
        return agents
    
    async def conduct_realtime_research(self, topic: str, focus: str, websocket: WebSocket, session_id: str):
        """Conduct research with real-time updates"""
        try:
            # Initialize session
            self.active_sessions[session_id] = {
                "topic": topic,
                "focus": focus,
                "start_time": datetime.now(),
                "results": {}
            }
            
            # Send start notification
            await websocket.send_text(json.dumps({
                "type": "research_started",
                "session_id": session_id,
                "topic": topic,
                "message": "Research team activated"
            }))
            
            # Phase 1: Parallel research by individual agents
            research_tasks = {
                "researcher": f"Research comprehensive background about {topic}. {focus if focus else ''}",
                "analyst": f"Analyze data, trends, and statistics for {topic}. {focus if focus else ''}",
                "news_tracker": f"Find recent news and developments about {topic}. {focus if focus else ''}"
            }
            
            # Run agents in parallel with real-time updates
            tasks = []
            for agent_id, query in research_tasks.items():
                task = asyncio.create_task(
                    self.agents[agent_id].research_async(query, websocket, agent_id)
                )
                tasks.append(task)
            
            # Wait for all individual research to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for i, agent_id in enumerate(research_tasks.keys()):
                if not isinstance(results[i], Exception):
                    self.active_sessions[session_id]["results"][agent_id] = results[i]
            
            # Phase 2: Synthesis (after individual research completes)
            synthesis_query = f"""
            Based on research about {topic}, synthesize these findings:
            
            Background: {self.active_sessions[session_id]["results"].get("researcher", "No data")}
            Analysis: {self.active_sessions[session_id]["results"].get("analyst", "No data")}
            News: {self.active_sessions[session_id]["results"].get("news_tracker", "No data")}
            
            Provide a comprehensive summary combining all insights.
            """
            
            synthesis_result = await self.agents["synthesizer"].research_async(
                synthesis_query, websocket, "synthesizer"
            )
            
            self.active_sessions[session_id]["results"]["synthesizer"] = synthesis_result
            
            # Send completion notification
            await websocket.send_text(json.dumps({
                "type": "research_completed",
                "session_id": session_id,
                "message": "All research completed successfully"
            }))
            
        except Exception as e:
            logger.error(f"Error in research: {str(e)}")
            await websocket.send_text(json.dumps({
                "type": "research_error",
                "session_id": session_id,
                "error": str(e)
            }))

# FastAPI app
app = FastAPI(title="Real-Time AI Research System")

# Initialize research team
research_team = RealTimeResearchTeam()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "start_research":
                topic = message.get("topic", "")
                focus = message.get("focus", "")
                
                if not topic:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Topic is required"
                    }))
                    continue
                
                # Start research in background
                asyncio.create_task(
                    research_team.conduct_realtime_research(
                        topic, focus, websocket, session_id
                    )
                )
            
            elif message["type"] == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
        if session_id in research_team.active_sessions:
            del research_team.active_sessions[session_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

@app.get("/")
async def get_homepage():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-Time AI Research System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .header { text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .agents { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
            .agent { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }
            .agent.active { border-left-color: #28a745; background: #d4edda; }
            .agent.completed { border-left-color: #6c757d; background: #e2e3e5; }
            .results { margin-top: 20px; }
            .result-section { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .status { font-weight: bold; color: #666; }
            .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; }
            .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔬 Real-Time AI Research System</h1>
                <p>Watch AI agents research your topic in real-time</p>
            </div>
            
            <div class="form-group">
                <label>Research Topic:</label>
                <input type="text" id="topic" placeholder="e.g., Climate Change Impact on Agriculture">
            </div>
            
            <div class="form-group">
                <label>Focus (optional):</label>
                <textarea id="focus" rows="3" placeholder="Specific aspects to focus on..."></textarea>
            </div>
            
            <button onclick="startResearch()">Start Real-Time Research</button>
            
            <div class="agents">
                <div class="agent" id="researcher">
                    <h3>🔍 Primary Researcher</h3>
                    <div class="status" id="researcher-status">Ready</div>
                </div>
                <div class="agent" id="analyst">
                    <h3>📊 Data Analyst</h3>
                    <div class="status" id="analyst-status">Ready</div>
                </div>
                <div class="agent" id="news_tracker">
                    <h3>📰 News Tracker</h3>
                    <div class="status" id="news_tracker-status">Ready</div>
                </div>
                <div class="agent" id="synthesizer">
                    <h3>🔄 Synthesizer</h3>
                    <div class="status" id="synthesizer-status">Ready</div>
                </div>
            </div>
            
            <div class="results" id="results"></div>
        </div>
        
        <script>
            let ws;
            let isConnected = false;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    isConnected = true;
                    console.log('WebSocket connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    isConnected = false;
                    console.log('WebSocket disconnected');
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function handleMessage(data) {
                const resultsDiv = document.getElementById('results');
                
                switch(data.type) {
                    case 'research_started':
                        resultsDiv.innerHTML = '<div class="success">Research started for: ' + data.topic + '</div>';
                        break;
                        
                    case 'agent_status':
                        const agentDiv = document.getElementById(data.agent_id);
                        const statusDiv = document.getElementById(data.agent_id + '-status');
                        
                        if (data.status === 'researching') {
                            agentDiv.className = 'agent active';
                            statusDiv.textContent = 'Researching...';
                        } else if (data.status === 'completed') {
                            agentDiv.className = 'agent completed';
                            statusDiv.textContent = 'Completed';
                        }
                        break;
                        
                    case 'research_result':
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-section';
                        resultDiv.innerHTML = `
                            <h3>${data.agent_name}</h3>
                            <p>${data.result}</p>
                            <small>Received: ${new Date().toLocaleTimeString()}</small>
                        `;
                        resultsDiv.appendChild(resultDiv);
                        break;
                        
                    case 'research_completed':
                        resultsDiv.insertAdjacentHTML('beforeend', '<div class="success">All research completed!</div>');
                        break;
                        
                    case 'agent_error':
                    case 'research_error':
                        resultsDiv.insertAdjacentHTML('beforeend', `<div class="error">Error: ${data.error}</div>`);
                        break;
                }
            }
            
            function startResearch() {
                if (!isConnected) {
                    alert('WebSocket not connected. Please refresh the page.');
                    return;
                }
                
                const topic = document.getElementById('topic').value;
                const focus = document.getElementById('focus').value;
                
                if (!topic.trim()) {
                    alert('Please enter a research topic');
                    return;
                }
                
                // Reset UI
                document.getElementById('results').innerHTML = '';
                const agents = ['researcher', 'analyst', 'news_tracker', 'synthesizer'];
                agents.forEach(agent => {
                    document.getElementById(agent).className = 'agent';
                    document.getElementById(agent + '-status').textContent = 'Ready';
                });
                
                // Start research
                ws.send(JSON.stringify({
                    type: 'start_research',
                    topic: topic,
                    focus: focus
                }));
            }
            
            // Connect WebSocket on page load
            window.addEventListener('load', connectWebSocket);
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    print("Starting Real-Time AI Research System...")
    print("Make sure to set your OpenAI API key: export OPENAI_API_KEY='your-key'")
    print("Optional: Set Tavily API key: export TAVILY_API_KEY='your-key'")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)