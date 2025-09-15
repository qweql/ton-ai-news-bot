# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from config import SUPABASE_URL, SUPABASE_KEY
import numpy as np

# Настройка страницы
st.set_page_config(
    page_title="TON AI Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Подключение к БД
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=SUPABASE_URL.replace("https://", "").split('.')[0],
        database="postgres",
        user="postgres",
        password=SUPABASE_KEY,
        port=5432
    )

conn = init_connection()

# Заголовок
st.title("📊 TON AI Analytics Dashboard")
st.markdown("Реал-тайм мониторинг экосистемы TON")

# Метрики
col1, col2, col3, col4 = st.columns(4)

with col1:
    price = pd.read_sql("SELECT price_usd FROM price_history ORDER BY created_at DESC LIMIT 1", conn)
    st.metric("Текущая цена", f"${price.iloc[0,0]:.2f}")

with col2:
    change = pd.read_sql("SELECT change_24h FROM price_history ORDER BY created_at DESC LIMIT 1", conn)
    st.metric("Изменение 24ч", f"{change.iloc[0,0]:.2f}%")

with col3:
    sentiment = pd.read_sql("SELECT sentiment FROM posted_news ORDER BY created_at DESC LIMIT 1", conn)
    st.metric("Тон последней новости", sentiment.iloc[0,0] if not sentiment.empty else "N/A")

with col4:
    accuracy = pd.read_sql("""
        SELECT AVG(CAST(is_correct AS INT)) * 100 as accuracy 
        FROM prediction_accuracy 
        WHERE is_correct IS NOT NULL
    """, conn)
    st.metric("Точность прогнозов", f"{accuracy.iloc[0,0]:.1f}%" if not accuracy.empty else "N/A")

# Графики
tab1, tab2, tab3 = st.tabs(["Цена TON", "Анализ новостей", "NFT Статистика"])

with tab1:
    st.subheader("История цены TON")
    price_data = pd.read_sql("""
        SELECT created_at, price_usd, change_24h 
        FROM price_history 
        WHERE created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at
    """, conn)
    
    fig = px.line(price_data, x='created_at', y='price_usd', 
                 title='Цена TON за 7 дней')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Анализ тональности новостей")
    news_data = pd.read_sql("""
        SELECT created_at, sentiment, confidence 
        FROM posted_news 
        WHERE created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at
    """, conn)
    
    if not news_data.empty:
        fig = px.scatter(news_data, x='created_at', y='confidence', 
                        color='sentiment', size='confidence',
                        title='Тональность новостей во времени')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Топ NFT коллекции")
    # Здесь можно добавить данные из NFT анализатора
    st.info("NFT данные обновляются каждые 6 часов")

# Прогнозы
st.subheader("🤖 AI Прогнозы на следующие 6 часов")
try:
    from ml_predictor import TONPredictor
    predictor = TONPredictor()
    features = predictor.get_current_features()
    
    if features:
        prediction, confidence = predictor.predict_future_price(features)
        st.metric("Предсказанное изменение", f"{prediction:.2f}%", 
                 delta_color="inverse" if prediction < 0 else "normal")
        st.progress(float(confidence), text=f"Уверенность модели: {confidence:.0%}")
    else:
        st.warning("Недостаточно данных для прогноза")
except Exception as e:
    st.error(f"Ошибка прогнозирования: {e}")

# Последние новости
st.subheader("📰 Последние новости")
recent_news = pd.read_sql("""
    SELECT title, sentiment, confidence, created_at 
    FROM posted_news 
    ORDER BY created_at DESC 
    LIMIT 10
""", conn)

for _, row in recent_news.iterrows():
    with st.expander(f"{row['title'][:50]}... ({row['sentiment']})"):
        st.write(f"Тон: {row['sentiment']}")
        st.write(f"Уверенность: {row['confidence']:.2f}")
        st.write(f"Время: {row['created_at']}")
