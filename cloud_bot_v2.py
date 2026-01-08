import requests
import os
import time
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. 从环境变量里拿钥匙 (安全！) ---
# 机器人运行时，会去 GitHub 的保险箱里找这两个变量
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 错误：没找到密钥！请检查 GitHub Secrets 设置。")
    exit(1)

# 连接数据库
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 目标币种
target_coins = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "DOGE_USDT"]

print("🚀 云端数据库爬虫启动...")

try:
    # --- 2. 获取时间 (北京时间) ---
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    current_time = beijing_now.strftime("%Y-%m-%d %H:%M:%S")

    # --- 3. 循环抓取 ---
    for coin in target_coins:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={coin}"
        
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            price = float(data[0]['last'])
            symbol = data[0]['currency_pair']
            
            print(f"💰 {symbol}: ${price:,.2f}")
            
            # --- 4. 直接写入云端数据库 ---
            # 准备数据字典
            row = {
                "time": current_time,
                "symbol": symbol,
                "price": price
            }
            
            # 写入 prices 表
            supabase.table("prices").insert(row).execute()
            print(f"  ✅ 已同步至 Supabase")

        except Exception as e:
            print(f"  ⚠️ 获取 {coin} 失败: {e}")
        
        time.sleep(1)

    print("🎉 所有任务完成！")

except Exception as e:
    print(f"❌ 严重错误: {e}")
    exit(1)