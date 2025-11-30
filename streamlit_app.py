import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import load_config
from app.services.rss import RSSService
from app.services.brave_search import BraveSearchService
from app.services.jina_reader import JinaReaderService
from app.services.ai import AIService
from app.models import Stats, IntelligenceCategory

st.set_page_config(page_title="Market Opportunity Finder", page_icon="📊", layout="wide")

st.title("📊 Market Opportunity Finder")
st.markdown("Generate intelligent market insights from news and RSS feeds.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    custom_topic = st.text_input("Custom Topic (Optional)", help="Enter a specific topic to analyze. Leave empty for default configuration.")
    
    st.divider()
    
    run_button = st.button("Run Analysis", type="primary", use_container_width=True)
    
    st.info("Note: Analysis may take a few minutes depending on the number of articles.")

async def run_analysis(topic):
    status = st.status("Initializing...", expanded=True)
    
    # 1. Load Configuration
    try:
        settings = load_config()
        if topic:
            settings.industry_keywords = [topic]
            settings.target_markets = [] # Clear markets to trigger "past month" freshness in Brave service
            settings.rss_feeds = [] # Disable default RSS feeds
            status.write(f"🎯 Custom topic set: {topic}")
        
        status.write("✅ Configuration loaded")
    except Exception as e:
        status.update(label="Error loading configuration", state="error")
        st.error(f"Failed to load configuration: {e}")
        return

    # 2. Initialize Services
    try:
        rss_service = RSSService(settings)
        brave_service = BraveSearchService(settings) if settings.enable_brave_search else None
        jina_service = JinaReaderService() if settings.enable_jina_reader else None
        ai_service = AIService(settings)
        status.write("✅ Services initialized")
    except Exception as e:
        status.update(label="Error initializing services", state="error")
        st.error(f"Failed to initialize services: {e}")
        return

    # 3. Collect Intelligence
    all_articles = []
    
    # Brave Search
    if brave_service and settings.enable_brave_search:
        status.write("🔍 Collecting intelligence from Brave Search...")
        try:
            brave_articles = await brave_service.search_industry_news()
            all_articles.extend(brave_articles)
            status.write(f"✅ Brave Search: {len(brave_articles)} articles")
        except Exception as e:
            st.error(f"❌ Brave Search failed: {e}")
    
    # RSS Feeds
    if settings.enable_rss:
        status.write("📡 Collecting intelligence from RSS feeds...")
        try:
            rss_articles = await rss_service.fetch_all()
            all_articles.extend(rss_articles)
            status.write(f"✅ RSS Feeds: {len(rss_articles)} articles")
        except Exception as e:
            st.error(f"❌ RSS collection failed: {e}")

    # Deduplicate
    unique_articles = {article.link: article for article in all_articles}
    articles = list(unique_articles.values())
    status.write(f"📰 Total unique articles: {len(articles)}")

    if not articles:
        status.update(label="No articles found", state="warning")
        st.warning("No articles found to process.")
        return

    # 3.5 Enrich
    if jina_service and settings.enable_jina_reader:
        status.write("📖 Enriching articles with Jina Reader...")
        try:
            articles = await jina_service.enrich_articles(articles, max_concurrent=3)
            status.write("✅ Content enrichment complete")
        except Exception as e:
            st.warning(f"⚠️ Jina Reader enrichment failed (continuing anyway): {e}")

    # 4. Analyze and Report
    status.write("🤖 Analyzing articles with AI...")
    
    # Create a container for results
    st.divider()
    st.subheader("Analysis Results")
    results_container = st.container()
    
    semaphore = asyncio.Semaphore(5)
    
    # Stats
    stats = Stats()
    
    async def process_and_display(index, article):
        async with semaphore:
            try:
                analysis = await ai_service.analyze_article(article)
                
                if analysis:
                    # Update stats
                    category = analysis.category or IntelligenceCategory.OTHER
                    stats.by_category[category.value] = stats.by_category.get(category.value, 0) + 1
                    if analysis.importance_score and analysis.importance_score >= 7:
                        stats.high_priority_count += 1
                    
                    # Display result
                    with results_container:
                        priority_icon = "🔥" if analysis.importance_score >= 8 else "⭐" if analysis.importance_score >= 6 else "📄"
                        with st.expander(f"{priority_icon} [{analysis.importance_score}/10] {article.title}", expanded=analysis.importance_score >= 7):
                            st.markdown(analysis.summary, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.caption(f"**Category:** {category.value}")
                                st.caption(f"**Score:** {analysis.importance_score}/10")
                            with col2:
                                st.caption(f"**Source:** {article.source}")
                                st.caption(f"**Date:** {article.published}")
                            
                            st.markdown(f"[🔗 Read Original Article]({article.link})")
                    return True
            except Exception as e:
                # st.error(f"Error processing article: {e}")
                pass
            return False

    tasks = [process_and_display(i, article) for i, article in enumerate(articles, 1)]
    results = await asyncio.gather(*tasks)
    
    stats.processed = sum(1 for r in results if r)
    stats.failed = len(articles) - stats.processed
    
    status.update(label="Analysis Complete", state="complete", expanded=False)
    
    # Show summary metrics
    st.sidebar.divider()
    st.sidebar.header("Summary")
    st.sidebar.metric("Total Articles", stats.total_articles)
    st.sidebar.metric("Processed", stats.processed)
    st.sidebar.metric("High Priority", stats.high_priority_count)

if run_button:
    asyncio.run(run_analysis(custom_topic))
