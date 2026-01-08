import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client, Client
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 云端投研室", page_icon="🧠", layout="wide")
st.title("🧠 AI 云端量化投研室")

# --- 🔐 安全连接：获取所有密钥 ---
try:
    # 数据库密钥
    SUPA_URL = st.secrets["supabase"]["url"]
    SUPA_KEY = st.secrets["supabase"]["key"]
    # AI 密钥
    AI_KEY = st.secrets["deepseek"]["api_key"]
    AI_BASE = st.secrets["deepseek"]["base_url"]
    
    # 初始化客户端
    supabase: Client = create_client(SUPA_URL, SUPA_KEY)
    
except Exception as e:
    st.error("❌ 密钥配置错误！请检查 Streamlit Secrets。")
    st.stop()

# --- 🔄 刷新按钮 ---
if st.button("🔄 刷新全网数据"):
    st.rerun()

# --- 📥 核心：从云端读数据 ---
@st.cache_data(ttl=60)
def load_data():
    # 读最近 100 条数据
    response = supabase.table("prices").select("*").order("time", desc=True).limit(100).execute()
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
                        # 1. 准备数据文本
                        data_str = df_coin.tail(15).to_string(index=False)
                        
                        # 2. 呼叫 AI
                        client = OpenAI(api_key=AI_KEY, base_url=AI_BASE)
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "你是一个资深加密货币分析师。根据提供的时间序列数据（最近15个点），分析价格动能、支撑压力位。输出格式要求：1. 趋势判断（看涨/看跌/震荡）；2. 关键点位；3. 操作建议。字数控制在150字以内。"},
                                {"role": "user", "content": f"数据如下：\n{data_str}"}
                            ]
                        )
                        
                        # 3. 展示
                        report = response.choices[0].message.content
                        st.success("研报生成完毕！")
                        st.info(report)
                        
                    except Exception as ai_e:
                        st.error(f"AI 调用失败: {ai_e}")

            # --- 原始数据 ---
            with st.expander("查看源数据"):
                st.dataframe(df_coin.sort_index(ascending=False))
        else:
            st.warning("该币种暂无数据。")
    else:
        st.info("☁️ 云数据库为空，等待机器人投喂数据中...")

except Exception as e:
    st.error(f"系统错误: {e}")
