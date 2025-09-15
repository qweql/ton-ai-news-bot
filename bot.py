# bot.py (финальная версия)
import time
from config import BOT_TOKEN, CHANNEL_ID, NEWS_LIMIT
from database import Database
from nft_analyzer import NFTAnalyzer
from gift_analyzer import GiftAnalyzer
from ml_predictor import TONPredictor
from alert_system import AlertSystem
from transformers import pipeline
import requests
import feedparser
from telegram import Bot
from telegram.error import TelegramError
import os

print("🚀 Запуск TON AI Analytics Platform...")

# Инициализация всех компонентов
db = Database()
nft_analyzer = NFTAnalyzer()
gift_analyzer = GiftAnalyzer()
predictor = TONPredictor()
alert_system = AlertSystem()
sentiment_analyzer = pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')

def main():
    try:
        print("🔍 Проверка оповещений...")
        alert_system.check_price_alerts()
        alert_system.check_volume_alerts()
        
        print("📊 Сбор рыночных данных...")
        price_data = get_ton_price()
        db.add_price_data(*price_data)
        
        print("🖼️ Анализ NFT...")
        nft_collections = nft_analyzer.get_top_nft_collections()
        nft_report = nft_analyzer.analyze_nft_trends(nft_collections)
        
        print("🎁 Анализ гифт-ботов...")
        gift_report = gift_analyzer.analyze_all_gifts()
        
        print("🤖 Генерация прогнозов...")
        features = predictor.get_current_features()
        if features:
            prediction, confidence = predictor.predict_future_price(features)
            prediction_text = f"📈 Прогноз на 6ч: {prediction:+.2f}% (уверенность: {confidence:.0%})"
        else:
            prediction_text = "📊 Прогноз: недостаточно данных"
        
        print("📰 Анализ новостей...")
        news_items = get_crypto_news()
        
        # Комплексный отчет
        send_comprehensive_report(price_data, nft_report, gift_report, prediction_text)
        
        # Обработка новостей
        for news in news_items[:NEWS_LIMIT]:
            if not db.is_news_posted(news['url']):
                process_and_send_news(news, price_data)
                time.sleep(10)
                
        print("✅ Все задачи выполнены!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

# ... (остальные функции остаются без изменений)
