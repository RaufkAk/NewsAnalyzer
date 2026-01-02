import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.repository import DatabaseManager
from analyzer.sentiment import NewsAnalyzer

st.set_page_config(page_title="Anahtar Kelimeler", page_icon="🔑", layout="wide")

st.markdown("""
    <style>
    .main { background: white; }
    h1, h2, h3 { color: #555 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    [data-testid="stSidebar"] .stMarkdown { color: #333; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    [data-testid="stSidebar"] > div:first-child::before {
        content: "📰 News Analyzer"; display: block; font-size: 1.5rem;
        font-weight: 700; color: #667eea; text-align: center;
        padding: 1rem 0; border-bottom: 2px solid #e0e0e0;
        margin-bottom: 1.5rem; position: absolute; top: 0;
        left: 0; right: 0; background: #f8f9fa; z-index: 999;
    }
    </style>
""", unsafe_allow_html=True)

db = DatabaseManager('news.db')
analyzer = NewsAnalyzer()

df = db.dbGetAllArticles(limit=1000)
if not df.empty:
    df = analyzer.analyze_batch(df)

st.markdown("""
    <div style='text-align: center; padding: 20px; background: rgba(102, 126, 234, 0.1); border-radius: 15px; margin-bottom: 20px; border: 2px solid rgba(102, 126, 234, 0.3);'>
        <h1 style='margin:0; font-size: 3em; color: #667eea;'>🔑 Anahtar Kelimeler</h1>
        <p style='color: #555; font-size: 1.2em; margin: 10px 0 0 0;'>Trending konular ve popüler kelimeler</p>
    </div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ Henüz veri yok!")
    st.stop()

st.subheader("🔥 Trending Konular")
trending = analyzer.get_trending_topics(df, top_n=15)

col1, col2, col3 = st.columns(3)

for idx, (topic, count) in enumerate(trending):
    with [col1, col2, col3][idx % 3]:
        st.metric(
            label=f"#{idx+1} {topic}",
            value=f"{count} haber"
        )

st.markdown("---")

st.subheader("📊 Kaynak Bazında Anahtar Kelimeler")

sources = df['source'].unique()

for source in sources:
    with st.expander(f"📰 {source}"):
        source_df = df[df['source'] == source]
        keywords = analyzer.extract_keywords(' '.join(source_df['title'].tolist()), top_n=10)
        
        cols = st.columns(5)
        for idx, (word, freq) in enumerate(keywords):
            with cols[idx % 5]:
                st.info(f"**{word}**\n{freq}x")