import requests
import os
import time
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. 获取密钥 ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL:
    print("❌ 未找到密钥，请检查 GitHub Secrets！")
    exit(1)

# 连接数据库
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 目标监控币种
target_coins = ["BTC_USDT", "ETH_USDT", "DOGE_USDT"]

# ================= 🤖 自动交易策略核心 =================
def auto_trade_logic(symbol, price):
    # 为了演示，我们只交易 BTC
    if symbol != "BTC_USDT":
        return

    print(f"  🤖 正在分析 {symbol} 交易机会...")

    # 1. 查余额
    resp = supabase.table("assets").select("*").execute()
    balance = {item['type']: item['amount'] for item in resp.data}
    
    usdt = balance.get("USDT", 0)
    btc = balance.get("BTC", 0)
    
    # 2. 简单策略 (你可以自己改！)
    # 比如：价格低于 90000 就买入，高于 95000 就卖出
    # 或者：无脑定投 (每次有多少U就买多少)
    
    # --- 模拟买入逻辑 (示例：只要有钱就买 10%) ---
    # 实际策略请根据你的需求修改，这里为了演示效果，设为：
    # "如果价格 < 92000 且我有钱，就用 10% 的钱买入"
    if price < 92000 and usdt > 10:
        spend_usdt = usdt * 0.1  # 每次只梭哈 10%
        buy_amount = spend_usdt / price
        
        # 更新数据库 (扣钱，加币)
        new_usdt = usdt - spend_usdt
        new_btc = btc + buy_amount
        
        supabase.table("assets").update({"amount": new_usdt}).eq("type", "USDT").execute()
        supabase.table("assets").update({"amount": new_btc}).eq("type", "BTC").execute()
        
        print(f"  ✅ [买入信号] 花费 ${spend_usdt:.2f} 买入 {buy_amount:.6f} BTC")

    # --- 模拟卖出逻辑 ---
    elif price > 98000 and btc > 0.001:
        sell_btc = btc * 0.5 # 卖一半
        get_usdt = sell_btc * price
        
        new_usdt = usdt + get_usdt
        new_btc = btc - sell_btc
        
        supabase.table("assets").update({"amount": new_usdt}).eq("type", "USDT").execute()
        supabase.table("assets").update({"amount": new_btc}).eq("type", "BTC").execute()
        
        print(f"  ✅ [卖出信号] 卖出 {sell_btc:.6f} BTC，获利 ${get_usdt:.2f}")
        
    else:
        print("  💤 暂无交易信号 (观望中)")
# =======================================================

print("🚀 云端全能机器人启动 (抓取+交易)...")

try:
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    current_time = beijing_now.strftime("%Y-%m-%d %H:%M:%S")

    for coin in target_coins:
        # 使用 Gate.io 接口
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={coin}"
        
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            price = float(data[0]['last'])
            symbol = data[0]['currency_pair']
            
            print(f"💰 {symbol}: ${price:,.2f}")
            
            # 1. 存入价格数据
            row = {"time": current_time, "symbol": symbol, "price": price}
            supabase.table("prices").insert(row).execute()
            
            # 2. 执行自动交易 (关键!)
            auto_trade_logic(symbol, price)

        except Exception as e:
            print(f"  ⚠️ 处理 {coin} 失败: {e}")
        
        time.sleep(1)

    print("🎉 任务全部完成！")

except Exception as e:
    print(f"❌ 严重错误: {e}")
    exit(1)
