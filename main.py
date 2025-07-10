# AI Research Team with LangChain
# Install required packages:
# pip install langchain langchain-openai langchain-community streamlit tavily-python wikipedia requests beautifulsoup4

import streamlit as st
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import asyncio
from datetime import datetime
import os

# Set up your API keys
# os.environ["OPENAI_API_KEY"] = "your-openai-key"
# os.environ["TAVILY_API_KEY"] = "your-tavily-key"

class ResearchAgent:
    def __init__(self, name: str, role: str, tools: List[Tool], llm: ChatOpenAI):
        self.name = name
        self.role = role
        self.tools = tools
        self.llm = llm
        self.agent = self._create_agent()
    
    def _create_agent(self):
        system_message = f"""You are {self.name}, a specialized research agent with the role: {self.role}.
        
        Your responsibilities:
        - Conduct thorough research on your assigned aspect of the topic
        - Provide accurate, well-sourced information
        - Summarize findings in a clear, structured format
        - Collaborate with other agents by sharing relevant insights
        
        Always cite your sources and provide actionable insights."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def research(self, query: str) -> str:
        try:
            result = self.agent.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Error in research: {str(e)}"

class ResearchTeam:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo")
        self.agents = self._create_agents()
    
    def _create_agents(self):
        # Create tools
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        # Tavily search tool (requires API key)
        try:
            tavily_search = TavilySearchResults(max_results=3)
        except:
            # Fallback if Tavily not available
            tavily_search = Tool(
                name="web_search",
                description="Search the web for information",
                func=lambda x: "Web search not available - please configure Tavily API key"
            )
        
        # Custom news search tool
        def search_news(query: str) -> str:
            try:
                # Using a simple news API or web scraping
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey=your-news-api-key"
                # For demo purposes, return a placeholder
                return f"Latest news about {query}: Recent developments and trends (Configure NewsAPI for real data)"
            except:
                return f"Unable to fetch news about {query}"
        
        news_tool = Tool(
            name="news_search",
            description="Search for recent news and developments",
            func=search_news
        )
        
        # Create specialized agents
        agents = {
            "researcher": ResearchAgent(
                name="Primary Researcher",
                role="Gather comprehensive background information and key facts",
                tools=[wikipedia, tavily_search],
                llm=self.llm
            ),
            "analyst": ResearchAgent(
                name="Data Analyst",
                role="Analyze trends, statistics, and quantitative aspects",
                tools=[tavily_search, news_tool],
                llm=self.llm
            ),
            "news_tracker": ResearchAgent(
                name="News Tracker",
                role="Find recent developments and current events",
                tools=[news_tool, tavily_search],
                llm=self.llm
            ),
            "synthesizer": ResearchAgent(
                name="Information Synthesizer",
                role="Combine and synthesize findings from all agents",
                tools=[],
                llm=self.llm
            )
        }
        
        return agents
    
    def conduct_research(self, topic: str) -> Dict[str, str]:
        """Coordinate research across all agents"""
        results = {}
        
        # Phase 1: Individual research
        research_tasks = {
            "researcher": f"Research comprehensive background information about {topic}. Include key facts, definitions, and historical context.",
            "analyst": f"Analyze data, trends, and statistics related to {topic}. Look for quantitative insights and patterns.",
            "news_tracker": f"Find recent news and developments about {topic}. Focus on current events and latest updates."
        }
        
        for agent_name, task in research_tasks.items():
            st.write(f"🔍 {self.agents[agent_name].name} is researching...")
            results[agent_name] = self.agents[agent_name].research(task)
        
        # Phase 2: Synthesis
        synthesis_prompt = f"""
        Based on the research conducted by the team about {topic}, synthesize the findings:
        
        Primary Research: {results.get('researcher', 'No data')}
        
        Data Analysis: {results.get('analyst', 'No data')}
        
        Recent News: {results.get('news_tracker', 'No data')}
        
        Provide a comprehensive summary that combines all findings into a coherent report.
        """
        
        st.write("🔄 Synthesizing findings...")
        results['synthesis'] = self.agents['synthesizer'].research(synthesis_prompt)
        
        return results

def main():
    st.set_page_config(page_title="AI Research Team", page_icon="🔬", layout="wide")
    
    st.title("🔬 AI Research Team")
    st.markdown("A collaborative team of AI agents conducting comprehensive research")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # API Key inputs
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
    tavily_key = st.sidebar.text_input("Tavily API Key (optional)", type="password")
    
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key
    
    # Main interface
    topic = st.text_input("Enter research topic:", placeholder="e.g., Artificial Intelligence in Healthcare")
    
    if st.button("Start Research", type="primary"):
        if not openai_key:
            st.error("Please provide your OpenAI API key in the sidebar")
            return
        
        if not topic:
            st.error("Please enter a research topic")
            return
        
        # Initialize research team
        with st.spinner("Initializing research team..."):
            team = ResearchTeam()
        
        # Conduct research
        st.header(f"Research Results: {topic}")
        
        with st.spinner("Research in progress..."):
            results = team.conduct_research(topic)
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Primary Research")
            st.write(results.get('researcher', 'No data available'))
            
            st.subheader("📊 Data Analysis")
            st.write(results.get('analyst', 'No data available'))
        
        with col2:
            st.subheader("📰 Recent News")
            st.write(results.get('news_tracker', 'No data available'))
        
        # Synthesis
        st.subheader("🔄 Comprehensive Summary")
        st.write(results.get('synthesis', 'No synthesis available'))
        
        # Export options
        st.subheader("Export Results")
        
        # Create downloadable report
        report = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        st.download_button(
            label="Download Research Report (JSON)",
            data=json.dumps(report, indent=2),
            file_name=f"research_report_{topic.replace(' ', '_')}.json",
            mime="application/json"
        )
    
    # Information about the agents
    st.sidebar.header("Research Team")
    st.sidebar.markdown("""
    **🔍 Primary Researcher**
    - Gathers background information
    - Provides historical context
    - Collects key facts and definitions
    
    **📊 Data Analyst**
    - Analyzes trends and statistics
    - Identifies quantitative patterns
    - Provides data-driven insights
    
    **📰 News Tracker**
    - Finds recent developments
    - Tracks current events
    - Monitors latest updates
    
    **🔄 Information Synthesizer**
    - Combines all findings
    - Creates comprehensive reports
    - Provides unified insights
    """)

if __name__ == "__main__":
    main()