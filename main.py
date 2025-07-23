import streamlit as st
import google.generativeai as genai
import time
from typing import List, Dict

def configure_genai(api_key: str):
    """Configure Google Generative AI with API key"""
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Error configuring Gemini API: {str(e)}")
        return False

def decomposer_agent(topic: str, model) -> List[str]:
    """Breaks the main topic into 3-5 sub-topics"""
    try:
        prompt = f"""
        You are a research decomposer agent. Break down the following research topic into 3-5 specific, focused sub-topics that would provide comprehensive coverage of the main topic.
        
        Topic: {topic}
        
        Return only the sub-topics as a numbered list, nothing else. Each sub-topic should be specific and researchable.
        """
        
        response = model.generate_content(prompt)
        subtopics = []
        
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and formatting
                clean_topic = line.split('.', 1)[-1].strip() if '.' in line else line.strip('- •').strip()
                if clean_topic:
                    subtopics.append(clean_topic)
        
        return subtopics[:5]  # Ensure max 5 subtopics
        
    except Exception as e:
        st.error(f"Error in DecomposerAgent: {str(e)}")
        return []

def research_agent(subtopic: str, model) -> str:
    """Researches a specific sub-topic and provides detailed information"""
    try:
        prompt = f"""
        You are a research agent. Conduct thorough research on the following sub-topic and provide a detailed, informative paragraph with key facts, statistics, and insights.
        
        Sub-topic: {subtopic}
        
        Provide a comprehensive paragraph (150-250 words) with factual information, current trends, and important details about this sub-topic. Focus on accuracy and depth.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Error researching {subtopic}: {str(e)}")
        return f"Error occurred while researching {subtopic}"

def summarizer_agent(topic: str, research_results: Dict[str, str], model) -> str:
    """Summarizes all research findings into a cohesive report"""
    try:
        research_text = ""
        for subtopic, research in research_results.items():
            research_text += f"\n\n**{subtopic}:**\n{research}"
        
        prompt = f"""
        You are a summarizer agent. Create a comprehensive, cohesive research report based on the following research findings about "{topic}".
        
        Research Findings:{research_text}
        
        Create a well-structured summary report that:
        1. Provides an executive summary
        2. Integrates all the research findings coherently
        3. Highlights key insights and connections between sub-topics
        4. Concludes with implications or future considerations
        
        The report should be 400-600 words and professionally written.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        st.error(f"Error in SummarizerAgent: {str(e)}")
        return "Error occurred while creating summary report"

def main():
    st.set_page_config(page_title="AI Research Team System", page_icon="🔬", layout="wide")
    
    st.title("🔬 AI Research Team System")
    st.markdown("*Powered by Google Gemini API*")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your Google Gemini API Key:", type="password", placeholder="Your API key here...")
        
        if api_key:
            if configure_genai(api_key):
                st.success("✅ API configured successfully!")
            else:
                st.error("❌ Invalid API key")
                return
        else:
            st.warning("Please enter your Gemini API key to continue")
            st.markdown("---")
            st.markdown("**How to get API key:**")
            st.markdown("1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)")
            st.markdown("2. Create a new API key")
            st.markdown("3. Copy and paste it above")
            st.markdown("Made with ❤️ by Bhaumik Snewal")
            
            return
    
    # Main interface
    st.header("Research Topic Input")
    topic = st.text_input("Enter your research topic:", placeholder="e.g., Artificial Intelligence in Healthcare")
    
    if st.button("🚀 Start Research", type="primary"):
        if not topic:
            st.error("Please enter a research topic")
            return
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Decompose topic
            status_text.text("🔍 DecomposerAgent: Breaking down the topic...")
            progress_bar.progress(20)
            
            subtopics = decomposer_agent(topic, model)
            
            if not subtopics:
                st.error("Failed to decompose the topic. Please try again.")
                return
            
            st.subheader("📋 Sub-topics Identified")
            for i, subtopic in enumerate(subtopics, 1):
                st.write(f"{i}. {subtopic}")
            
            # Step 2: Research each sub-topic
            status_text.text("📚 ResearchAgent: Conducting detailed research...")
            progress_bar.progress(40)
            
            research_results = {}
            
            st.subheader("🔬 Research Results")
            
            for i, subtopic in enumerate(subtopics):
                with st.expander(f"Research: {subtopic}", expanded=True):
                    with st.spinner(f"Researching {subtopic}..."):
                        research_result = research_agent(subtopic, model)
                        research_results[subtopic] = research_result
                        st.write(research_result)
                
                # Update progress
                progress_value = 40 + (i + 1) * (40 / len(subtopics))
                progress_bar.progress(int(progress_value))
                time.sleep(0.5)  # Small delay to show progress
            
            # Step 3: Summarize findings
            status_text.text("📝 SummarizerAgent: Creating comprehensive report...")
            progress_bar.progress(90)
            
            with st.spinner("Generating final summary..."):
                final_summary = summarizer_agent(topic, research_results, model)
            
            progress_bar.progress(100)
            status_text.text("✅ Research complete!")
            
            # Display final summary
            st.subheader("📊 Final Research Report")
            st.markdown("---")
            st.markdown(final_summary)
            
            # Download option
            st.download_button(
                label="📥 Download Text Report",
                data=f"# Research Report: {topic}\n\n{final_summary}",
                file_name=f"research_report_{topic.replace(' ', '_')}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"An error occurred during research: {str(e)}")
            st.info("Please check your API key and try again.")

if __name__ == "__main__":
    main()
