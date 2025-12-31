import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.append(str(Path(__file__).parent.parent))

from database.repository import DatabaseManager
from analyzer.sentiment import NewsAnalyzer
from dashboard.components import DashboardUI

st.set_page_config(page_title="Trend Analizi", page_icon="📈", layout="wide")

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
ui = DashboardUI()

df = db.dbGetAllArticles(limit=1000)
if not df.empty:
    df = analyzer.analyze_batch(df)

st.markdown("""
    <div style='text-align: center; padding: 20px; background: rgba(102, 126, 234, 0.1); border-radius: 15px; margin-bottom: 20px; border: 2px solid rgba(102, 126, 234, 0.3);'>
        <h1 style='margin:0; font-size: 3em; color: #667eea;'>📈 Trend Analizi</h1>
        <p style='color: #555; font-size: 1.2em; margin: 10px 0 0 0;'>Zaman serisi ve trend grafikleri</p>
    </div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("⚠️ Henüz veri yok!")
    st.stop()

st.subheader("📈 Zaman İçinde Duygu Trendi")
ui.plot_sentiment_timeline(df)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Günlük Haber Sayısı")
    df['day'] = pd.to_datetime(df['date']).dt.date
    df['day_name'] = pd.to_datetime(df['date']).dt.day_name()
    
    daily_dist = df['day_name'].value_counts()
    
    fig = px.bar(x=daily_dist.index, y=daily_dist.values,
                 labels={'x': 'Gün', 'y': 'Haber Sayısı'},
                 color=daily_dist.values, color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⏰ Saatlik Dağılım")
    hourly_dist = pd.to_datetime(df['date']).dt.hour.value_counts().sort_index()
    
    fig = px.line(x=hourly_dist.index, y=hourly_dist.values,
                  labels={'x': 'Saat', 'y': 'Haber Sayısı'},
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Kaynak Performansı")
source_stats = analyzer.sentiment_by_source(df)
if not source_stats.empty:
    st.dataframe(source_stats, use_container_width=True)