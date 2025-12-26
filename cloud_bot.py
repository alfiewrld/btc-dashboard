import requests
import pandas as pd
import os
from datetime import datetime

# --- 1. 获取数据 (使用 CoinCap 接口，适合云端环境) ---
url = "https://api.coincap.io/v2/assets"
# 我们要查的币
target_coins = ["bitcoin", "ethereum", "solana", "dogecoin"]

print("🚀 云端爬虫开始工作...")

try:
    # 发送请求
    resp = requests.get(url, timeout=10)
    data = resp.json()["data"]
    
    # 准备一个列表装数据
    new_rows = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 遍历所有数据，找到我们要的币
    for item in data:
        coin_id = item["id"]
        if coin_id in target_coins:
            price = float(item["priceUsd"])
            symbol = item["symbol"]
            
            print(f"💰 {symbol}: ${price:,.2f}")
            
            # 加入列表
            new_rows.append({
                "时间": current_time,
                "币种": symbol,
                "价格": price
            })

    # --- 2. 存入 Excel ---
    # 注意：文件名要和 web_pro.py 里读取的一模一样！
    file_path = "全币种监控表.xlsx"

    # 如果文件存在，就读取旧数据
    if os.path.exists(file_path):
        df_old = pd.read_excel(file_path)
        df_new = pd.DataFrame(new_rows)
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = pd.DataFrame(new_rows)
    
    # 保存
    df_final.to_excel(file_path, index=False)
    print("✅ 数据已更新并保存！")

except Exception as e:
    print(f"❌ 出错了: {e}")