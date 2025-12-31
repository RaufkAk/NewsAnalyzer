import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


class DashboardUI:
    
    def render_header(self):
        st.markdown("""
            <div style='text-align: center; padding: 25px; background: rgba(0, 0, 0, 0.7); border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 16px rgba(0,0,0,0.4); border: 2px solid rgba(255,255,255,0.2);'>
                <h1 style='margin:0; font-size: 3.5em; color: white; text-shadow: 3px 3px 6px rgba(0,0,0,0.5); font-weight: 700;'>📊 News Sentiment Analyzer</h1>
            </div>
        """, unsafe_allow_html=True)

    def render_metrics(self, df: pd.DataFrame):
        if df.empty:
            return

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            today_count = len(df[df['date'] > datetime.now() - timedelta(days=1)])
            st.metric(
                label="📰 Toplam Haber",
                value=len(df),
                delta=f"+{today_count} (bugün)" if today_count > 0 else None
            )

        with col2:
            avg_sentiment = df['sentiment'].mean()
            st.metric(
                label="😊 Ortalama Duygu",
                value=f"{avg_sentiment:.3f}",
                delta="Pozitif ↑" if avg_sentiment > 0 else "Negatif ↓"
            )

        with col3:
            positive_count = (df['sentiment_label'] == 'Positive').sum()
            positive_pct = positive_count / len(df) * 100 if len(df) > 0 else 0
            st.metric(
                label="✅ Pozitif Oran",
                value=f"{positive_pct:.1f}%",
                delta=f"{positive_count} haber"
            )

        with col4:
            sources_count = df['source'].nunique()
            st.metric(
                label="📡 Kaynak Sayısı",
                value=sources_count,
                delta=f"{len(df) // max(sources_count, 1)} avg/kaynak"
            )

    def plot_sentiment_pie(self, df: pd.DataFrame):
        if df.empty:
            st.warning("Veri yok")
            return

        order = ['Positive', 'Neutral', 'Negative']
        labels_tr = ['Pozitif', 'Nötr', 'Negatif']
        values = [(df['sentiment_label'] == k).sum() for k in order]
        colors = ['#2ecc71', '#95a5a6', '#e74c3c']

        fig = go.Figure(data=[go.Pie(
            labels=labels_tr,
            values=values,
            hole=0.4,
            marker_colors=colors
        )])
        fig.update_layout(height=400, title="🎭 Duygu Dağılımı")
        st.plotly_chart(fig, use_container_width=True)

    def plot_source_distribution(self, df: pd.DataFrame):
        if df.empty:
            st.warning("Veri yok")
            return

        source_counts = df['source'].value_counts()

        fig = px.bar(
            x=source_counts.index,
            y=source_counts.values,
            labels={'x': 'Kaynak', 'y': 'Haber Sayısı'},
            color=source_counts.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400, showlegend=False, title="📡 Kaynak Bazında Haber Sayısı")
        st.plotly_chart(fig, use_container_width=True)

    def plot_source_sentiment_grouped(self, df: pd.DataFrame):
        if df.empty:
            st.warning("Veri yok")
            return

        label_map = {'Positive': 'Pozitif', 'Neutral': 'Nötr', 'Negative': 'Negatif'}
        df['sentiment_label_tr'] = df['sentiment_label'].map(label_map)
        source_sentiment = df.groupby(['source', 'sentiment_label_tr']).size().reset_index(name='count')

        fig = px.bar(
            source_sentiment,
            x='source',
            y='count',
            color='sentiment_label_tr',
            barmode='group',
            color_discrete_map={'Pozitif': '#2ecc71', 'Nötr': '#95a5a6', 'Negatif': '#e74c3c'},
            labels={'count': 'Haber Sayısı', 'source': 'Kaynak', 'sentiment_label_tr': 'Duygu'}
        )
        fig.update_layout(height=400, title="📊 Kaynak Bazında Duygu Analizi")
        st.plotly_chart(fig, use_container_width=True)

    def plot_sentiment_timeline(self, df: pd.DataFrame):
        if df.empty or 'date' not in df.columns:
            st.warning("Veri yok")
            return

        df['day'] = df['date'].dt.date
        daily_sentiment = df.groupby('day').agg({
            'sentiment': 'mean',
            'id': 'count'
        }).reset_index()
        daily_sentiment.columns = ['day', 'avg_sentiment', 'count']

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=daily_sentiment['day'],
            y=daily_sentiment['avg_sentiment'],
            name='Ortalama Duygu',
            line=dict(color='#e74c3c', width=3),
            mode='lines+markers'
        ))

        fig.add_trace(go.Bar(
            x=daily_sentiment['day'],
            y=daily_sentiment['count'],
            name='Haber Sayısı',
            yaxis='y2',
            opacity=0.3,
            marker_color='#3498db'
        ))

        fig.update_layout(
            height=500,
            title="📈 Zaman İçinde Duygu Trendi",
            yaxis=dict(title='Duygu Skoru', side='left'),
            yaxis2=dict(title='Haber Sayısı', side='right', overlaying='y'),
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    def plot_histogram(self, df: pd.DataFrame):
        if df.empty:
            st.warning("Veri yok")
            return

        fig = px.histogram(
            df,
            x='sentiment',
            nbins=30,
            color='sentiment_label',
            color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#95a5a6', 'Negative': '#e74c3c'},
            labels={'sentiment': 'Duygu Skoru', 'count': 'Frekans'}
        )
        fig.update_layout(height=400, title="📊 Sentiment Score Dağılımı")
        st.plotly_chart(fig, use_container_width=True)

    def plot_box_plot(self, df: pd.DataFrame):
        if df.empty:
            st.warning("Veri yok")
            return

        fig = px.box(
            df,
            x='source',
            y='sentiment',
            color='source',
            labels={'sentiment': 'Duygu Skoru', 'source': 'Kaynak'}
        )
        fig.update_layout(height=400, showlegend=False, title="📦 Kaynak Bazında Sentiment Dağılımı")
        st.plotly_chart(fig, use_container_width=True)

    def plot_keywords_bar(self, keywords: List[tuple]):
        if not keywords:
            st.warning("Anahtar kelime yok")
            return

        kw_df = pd.DataFrame(keywords[:20], columns=['word', 'count'])

        fig = px.bar(
            kw_df,
            x='count',
            y='word',
            orientation='h',
            color='count',
            color_continuous_scale='Viridis',
            labels={'count': 'Frekans', 'word': 'Kelime'}
        )
        fig.update_layout(height=600, showlegend=False, title="🔑 En Popüler Anahtar Kelimeler")
        st.plotly_chart(fig, use_container_width=True)

    def render_news_list(self, df: pd.DataFrame, sort_by: str = 'En Yeni'):
        if df.empty:
            st.warning("Haber yok")
            return

        if sort_by == 'En Yeni':
            df_display = df.sort_values('date', ascending=False)
        elif sort_by == 'En Pozitif':
            df_display = df.sort_values('sentiment', ascending=False)
        else:
            df_display = df.sort_values('sentiment', ascending=True)

        for idx, row in df_display.head(20).iterrows():
            if row['sentiment'] > 0.1:
                color, emoji = '🟢', '😊'
            elif row['sentiment'] < -0.1:
                color, emoji = '🔴', '😢'
            else:
                color, emoji = '🟡', '😐'

            with st.container():
                col1, col2, col3 = st.columns([0.5, 8, 1.5])

                with col1:
                    st.markdown(f"### {color}")

                with col2:
                    st.markdown(f"**{row['title']}**")
                    date_str = row['date'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['date']) else 'Tarih yok'
                    st.caption(f"📡 {row['source']} | 📅 {date_str}")
                    if row['url']:
                        st.markdown(f"[🔗 Haberi Oku]({row['url']})")

                with col3:
                    st.metric("Duygu", f"{row['sentiment']:.2f}", emoji)

                st.markdown("---")

    def render_footer(self):
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; color: gray;'>
            <p>📰 News Analyzer Dashboard | Made with ❤️ using Streamlit</p>
            <p>Son güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar_filters(self, df: pd.DataFrame) -> Dict:
        st.sidebar.markdown("### 🎛️ Filtreler")

        filters = {}

        if not df.empty:
            sources = ['Tümü'] + sorted(df['source'].unique().tolist())
            filters['source'] = st.sidebar.selectbox("📡 Kaynak", sources)

            if 'date' in df.columns:
                min_date = df['date'].min().date()
                max_date = df['date'].max().date()

                if min_date != max_date:
                    filters['date_range'] = st.sidebar.date_input(
                        "📅 Tarih Aralığı",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )

            filters['sentiment'] = st.sidebar.multiselect(
                "😊 Duygu",
                ['Positive', 'Neutral', 'Negative'],
                default=['Positive', 'Neutral', 'Negative']
            )

        return filters

    def apply_filters(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        if df.empty:
            return df

        if filters.get('source') and filters['source'] != 'Tümü':
            df = df[df['source'] == filters['source']]

        if 'date_range' in filters and len(filters['date_range']) == 2:
            df = df[
                (df['date'].dt.date >= filters['date_range'][0]) &
                (df['date'].dt.date <= filters['date_range'][1])
            ]

        if filters.get('sentiment'):
            df = df[df['sentiment_label'].isin(filters['sentiment'])]

        return df