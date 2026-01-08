import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client, Client
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 云端投研室", page_icon="🧠", layout="wide")
st.title("🧠 AI 云端量化投研室 (含实盘账户)")

# --- 🔐 安全连接 ---
try:
    SUPA_URL = st.secrets["supabase"]["url"]
    SUPA_KEY = st.secrets["supabase"]["key"]
    AI_KEY = st.secrets["deepseek"]["api_key"]
    AI_BASE = st.secrets["deepseek"]["base_url"]
    
    supabase: Client = create_client(SUPA_URL, SUPA_KEY)
    
except Exception as e:
    st.error("❌ 密钥配置错误！请检查 Streamlit Secrets。")
    st.stop()

# --- 🔄 刷新按钮 ---
if st.sidebar.button("🔄 刷新全网数据"):
    st.rerun()

# ================= 💼 新增：账户资产显示模块 =================
def show_my_assets():
    try:
        # 1. 从 Supabase 读取 assets 表
        resp = supabase.table("assets").select("*").execute()
        
        # 把数据转换成字典，方便取值: {'USDT': 100000, 'BTC': 0.5}
        my_assets = {item['type']: item['amount'] for item in resp.data}
        
        usdt_balance = my_assets.get("USDT", 0)
        btc_balance = my_assets.get("BTC", 0)

        # 2. 获取 BTC 当前价格 (为了计算总资产值多少钱)
        # 我们专门查一下最新的 BTC_USDT 价格
        price_resp = supabase.table("prices").select("price").eq("symbol", "BTC_USDT").order("time", desc=True).limit(1).execute()
        
        if price_resp.data:
            current_btc_price = price_resp.data[0]['price']
        else:
            current_btc_price = 0 # 如果数据库空的，价格算0

        # 3. 计算总市值 (现金 + 币值)
        total_value = usdt_balance + (btc_balance * current_btc_price)

        # 4. 在侧边栏显示
        st.sidebar.divider()
        st.sidebar.header("💼 模拟实盘账户")
        st.sidebar.write(f"💵 **可用现金**: ${usdt_balance:,.2f}")
        st.sidebar.write(f"🪙 **持有 BTC**: {btc_balance:.6f} 个")
        
        # 显示总资产，并根据是否赚钱显示颜色
        delta_color = "normal"
        if total_value > 100000: delta_color = "normal" # 赚钱了
        st.sidebar.metric("💰 账户总净值", f"${total_value:,.2f}", delta=f"{total_value-100000:+.2f}")
        st.sidebar.divider()

    except Exception as e:
        st.sidebar.error(f"无法读取账户信息: {e}")

# 运行这个显示函数
show_my_assets()
# ==========================================================

# --- 📥 核心：从云端读数据 ---
@st.cache_data(ttl=60)
def load_data():
    response = supabase.table("prices").select("*").order("time", desc=True).limit(200).execute()
    return pd.DataFrame(response.data)

# === 主程序 ===
try:
    df = load_data()

    if not df.empty:
        df["time"] = pd.to_datetime(df["time"])
        
        # 侧边栏选择
        coin_list = df["symbol"].unique()
        selected_coin = st.sidebar.selectbox("👉 选择分析币种:", coin_list)
        
        # 数据切片
        df_coin = df[df["symbol"] == selected_coin].sort_values(by="time")
        
        if not df_coin.empty:
            # --- 📊 展示行情 ---
            latest_price = df_coin["price"].iloc[-1]
            
            # 计算涨跌幅
            if len(df_coin) > 1:
                prev = df_coin["price"].iloc[-2]
                change = (latest_price - prev) / prev * 100
                st.metric(f"{selected_coin} 实时报价", f"${latest_price:,.4f}", f"{change:.2f}%")
            else:
                st.metric(f"{selected_coin} 实时报价", f"${latest_price:,.4f}")

            # --- 📈 画图 ---
            st.subheader("📈 价格走势")
            c = alt.Chart(df_coin).mark_line(point=True).encode(
                x=alt.X('time', axis=alt.Axis(format='%m-%d %H:%M', title='时间')),
                y=alt.Y('price', scale=alt.Scale(zero=False)),
                tooltip=['time', 'price']
            ).interactive()
            st.altair_chart(c, use_container_width=True)

            # --- 🧠 AI 分析模块 ---
            st.divider()
            st.subheader(f"🧠 AI 首席分析师 ({selected_coin})")
            
            if st.button("✨ 生成研报"):
                with st.spinner("AI 正在读取云端数据库并进行分析..."):
                    try:
                        data_str = df_coin.tail(15).to_string(index=False)
                        client = OpenAI(api_key=AI_KEY, base_url=AI_BASE)
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "你是一个资深加密货币分析师。根据提供的时间序列数据，分析价格动能。输出格式：1.趋势判断；2.关键点位；3.操作建议。"},
                                {"role": "user", "content": f"数据如下：\n{data_str}"}
                            ]
                        )
                        st.success("分析完成！")
                        st.info(response.choices[0].message.content)
                    except Exception as ai_e:
                        st.error(f"AI 调用失败: {ai_e}")

            with st.expander("查看源数据"):
                st.dataframe(df_coin.sort_index(ascending=False))
        else:
            st.warning("该币种暂无数据。")
    else:
        st.info("☁️ 云数据库为空，等待机器人投喂数据中...")

except Exception as e:
    st.error(f"系统错误: {e}")
