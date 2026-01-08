import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client, Client
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="Cloud BTC 看板", page_icon="☁️", layout="wide")
st.title("☁️ 全币种云端监控室 (Supabase驱动)")

# --- 🔐 连接 Supabase (使用 Streamlit Secrets) ---
# 这里的代码会自动去你刚才设置的 Secrets 里找密码，非常安全
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("❌ 没找到密钥！请在 Streamlit Settings -> Secrets 里配置 supabase url 和 key。")
    st.stop()

# --- 🔄 刷新按钮 ---
if st.button("🔄 刷新最新数据"):
    st.rerun()

# --- 📥 核心函数：从云端读数据 ---
@st.cache_data(ttl=60) # 加个缓存，60秒内不重复请求，省流量
def load_data_from_cloud():
    # SQL翻译：从 prices 表里选所有数据，按时间倒序，取最近 500 条
    response = supabase.table("prices").select("*").order("time", desc=True).limit(500).execute()
    data = response.data
    return pd.DataFrame(data)

# === 主程序 ===
try:
    df = load_data_from_cloud()

    if not df.empty:
        # 转换时间格式 (防止报错)
        df["time"] = pd.to_datetime(df["time"])
        
        # --- 侧边栏 ---
        coin_list = df["symbol"].unique()
        selected_coin = st.sidebar.selectbox("👉 选择币种:", coin_list)
        
        # 筛选数据
        df_coin = df[df["symbol"] == selected_coin].sort_values(by="time")

        # --- 展示指标 ---
        latest_price = df_coin["price"].iloc[-1]
        st.metric(f"{selected_coin} 最新云端报价", f"${latest_price:,.4f}")

        # --- 画图 ---
        st.subheader(f"📈 {selected_coin} 实时走势")
        
        c = alt.Chart(df_coin).mark_line(point=True).encode(
            x=alt.X('time', axis=alt.Axis(format='%m-%d %H:%M', title='时间')),
            y=alt.Y('price', scale=alt.Scale(zero=False), title='价格'),
            tooltip=['time', 'price']
        ).interactive()
        
        st.altair_chart(c, use_container_width=True)

        # --- 数据表 ---
        with st.expander("查看云端数据库源数据"):
            st.dataframe(df_coin.sort_index(ascending=False))

    else:
        st.warning("云数据库里还没有数据，请等待 GitHub 机器人运行...")

except Exception as e:
    st.error(f"读取失败: {e}")
