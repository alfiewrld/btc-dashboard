import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta # 👈 引入时间计算工具

# 目标币种
target_coins = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "DOGE_USDT"]

print("🚀 云端爬虫开始工作 (Gate.io版)...")

try:
    # --- 🕒 核心修改 1：校准时区 ---
    # 获取 UTC 时间，然后强行 +8 小时 = 北京时间
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    current_time = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    
    new_rows = []

    for coin in target_coins:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={coin}"
        
        try:
            # 发送请求
            resp = requests.get(url, timeout=10)
            data = resp.json()
            price = float(data[0]['last'])
            symbol = data[0]['currency_pair']
            
            print(f"💰 {symbol}: ${price:,.2f}")
            
            new_rows.append({
                "时间": current_time, # 使用校准后的北京时间
                "币种": symbol,
                "价格": price
            })
        except Exception as e:
            print(f"⚠️ 获取 {coin} 失败，跳过: {e}")
            # 单个币失败不要紧，继续抓下一个
            continue
        
        time.sleep(1)

    # --- 2. 存入 Excel ---
    if len(new_rows) > 0: # 只有抓到了数据才存
        file_path = "data.xlsx"

        if os.path.exists(file_path):
            df_old = pd.read_excel(file_path)
            df_new = pd.DataFrame(new_rows)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = pd.DataFrame(new_rows)
        
        df_final.to_excel(file_path, index=False)
        print("✅ 数据已更新并保存！")
    else:
        print("⚠️ 本轮没有抓到任何数据，跳过保存。")

except Exception as e:
    print(f"❌ 严重错误: {e}")
    exit(1)
