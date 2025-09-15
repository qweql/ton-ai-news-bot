# alert_system.py
from telegram import Bot
from config import BOT_TOKEN, CHANNEL_ID
import pandas as pd
import psycopg2
from config import SUPABASE_URL, SUPABASE_KEY

class AlertSystem:
    def init(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.conn = psycopg2.connect(
            host=SUPABASE_URL.replace("https://", "").split('.')[0],
            database="postgres",
            user="postgres",
            password=SUPABASE_KEY,
            port=5432
        )

    def check_price_alerts(self):
        """Проверяет резкие изменения цены"""
        query = """
        SELECT price_usd, change_24h, created_at 
        FROM price_history 
        ORDER BY created_at DESC 
        LIMIT 2
        """
        
        df = pd.read_sql(query, self.conn)
        if len(df) < 2:
            return
        
        current = df.iloc[0]
        previous = df.iloc[1]
        
        price_change = abs(current['price_usd'] - previous['price_usd']) / previous['price_usd'] * 100
        
        if price_change > 5:  # 5% изменение за период
            self.send_alert(
                f"🚨 Резкое движение цены!\n"
                f"Изменение: {price_change:.1f}%\n"
                f"Текущая цена: ${current['price_usd']:.2f}\n"
                f"Время: {current['created_at']}"
            )

    def check_volume_alerts(self):
        """Проверяет аномальные объемы торгов"""
        query = """
        SELECT volume_24h, created_at 
        FROM price_history 
        WHERE created_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at
        """
        
        df = pd.read_sql(query, self.conn)
        if len(df) < 2:
            return
        
        current_volume = df.iloc[0]['volume_24h']
        avg_volume = df['volume_24h'].mean()
        
        if current_volume > avg_volume * 2:  # Объем в 2 раза выше среднего
            self.send_alert(
                f"📊 Аномальный объем торгов!\n"
                f"Текущий объем: ${current_volume:,.0f}\n"
                f"Средний объем: ${avg_volume:,.0f}\n"
                f"Превышение: {current_volume/avg_volume:.1f}x"
            )

    def send_alert(self, message):
        """Отправляет оповещение в Telegram"""
        try:
            self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='HTML'
            )
            print(f"✅ Оповещение отправлено: {message[:50]}...")
        except Exception as e:
            print(f"❌ Ошибка отправки оповещения: {e}")
