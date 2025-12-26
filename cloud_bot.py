import requests
import pandas as pd
import os
import time
from datetime import datetime

# --- 改用 Gate.io 接口 (最稳) ---
# 我们要查的币种列表 (Gate的格式是 BTC_USDT)
target_coins = ["BTC_USDT", "ETH_USDT", "SOL_USDT", "DOGE_USDT"]

print("🚀 云端爬虫开始工作 (Gate.io版)...")

try:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_rows = []

    # 循环去查每一个币
    for coin in target_coins:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={coin}"
        
        # 发送请求
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        # Gate 返回的是列表 [{'currency_pair': 'BTC_USDT', 'last': '96000'}]
        price = float(data[0]['last'])
        symbol = data[0]['currency_pair'] # 比如 BTC_USDT
        
        print(f"💰 {symbol}: ${price:,.2f}")
        
        # 加入列表
        new_rows.append({
            "时间": current_time,
            "币种": symbol,
            "价格": price
        })
        
        # 稍微休息一下，防止请求太快
        time.sleep(1)

    # --- 2. 存入 Excel ---
    file_path = "全币种监控表.xlsx"

    # 如果文件存在，就读取旧数据
    if os.path.exists(file_path):
        df_old = pd.read_excel(file_path)
        df_new = pd.DataFrame(new_rows)
        # 合并
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = pd.DataFrame(new_rows)
    
    # 保存
    df_final.to_excel(file_path, index=False)
    print("✅ 数据已更新并保存！")

except Exception as e:
    print(f"❌ 严重错误: {e}")
    exit(1) # 依然保留报错退出机制，方便监控