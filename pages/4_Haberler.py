import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.repository import DatabaseManager
from analyzer.sentiment import NewsAnalyzer

st.set_page_config(page_title="🏠 Ana Sayfa", page_icon="🏠", layout="wide")

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
        <h1 style='margin:0; font-size: 3em; color: #667eea;'>📰 Tüm Haberler</h1>
        <p style='color: #555; font-size: 1.2em; margin: 10px 0 0 0;'>Haber listesi, arama ve filtreleme</p>
    </div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ Henüz veri yok!")
    st.stop()

sort_by = st.sidebar.selectbox(
    "Sıralama",
    ["Sentiment (↑)", "Sentiment (↓)"]
)

if "↑" in sort_by:
    df = df.sort_values('sentiment', ascending=False)
else:
    df = df.sort_values('sentiment', ascending=True)

page_size = 20
total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)
page = st.sidebar.number_input("Sayfa", min_value=1, max_value=max(1, total_pages), value=1)

start_idx = (page - 1) * page_size
end_idx = start_idx + page_size

st.info(f"📄 Sayfa {page}/{total_pages} | Toplam: {len(df)} haber")

for idx, row in df.iloc[start_idx:end_idx].iterrows():
    sentiment_color = "🟢" if row['sentiment'] > 0.2 else "🔴" if row['sentiment'] < -0.2 else "🟡"
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {sentiment_color} {row['title']}")
            st.caption(f"📰 {row['source']} | 📅 {row['date']}")
            if row['url']:
                st.markdown(f"[🔗 Haberi Oku]({row['url']})")
        
        with col2:
            st.metric("Sentiment", f"{row['sentiment']:.3f}")
            st.caption(row.get('sentiment_label', 'Neutral'))
        
        st.markdown("---")