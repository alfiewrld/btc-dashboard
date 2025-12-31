import streamlit as st
import pandas as pd
import os
import altair as alt
from openai import OpenAI # 👈 引入 AI 大脑

# ================= 🔐 配置区域 =================
# 把你的 DeepSeek Key 填在这里
API_KEY = "sk-b825fda5c5af4d94b2477bba91bf6601" 
BASE_URL = "https://api.deepseek.com"
# ==============================================

# 1. 页面配置
st.set_page_config(page_title="Crypto AI 量化终端", page_icon="🧠", layout="wide")
st.title("🧠 Crypto AI 量化终端")

# 2. 读取文件
file_path = "data.xlsx" # 确保文件名是对的

# 刷新按钮
if st.button("🔄 刷新数据"):
    st.rerun()

if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    
    if "币种" in df.columns:
        # --- 🕹 侧边栏：选择币种 ---
        coin_list = df["币种"].unique()
        selected_coin = st.sidebar.selectbox("👉 选择币种:", coin_list)
        
        # 数据清洗
        df_coin = df[df["币种"] == selected_coin]
        df_coin = df_coin.sort_values(by="时间")

        if not df_coin.empty:
            # --- 📊 展示指标 ---
            latest_price = df_coin["价格"].iloc[-1]
            
            # 计算涨跌
            if len(df_coin) > 1:
                prev_price = df_coin["价格"].iloc[-2]
                change = (latest_price - prev_price) / prev_price * 100
                color = "green" if change > 0 else "red"
                signal_icon = "📈" if change > 0 else "📉"
            else:
                change = 0
                color = "gray"
                signal_icon = "➖"

            st.divider()
            col1, col2 = st.columns(2)
            col1.metric(f"{selected_coin} 最新价", f"${latest_price:,.4f}")
            col1.markdown(f"#### 24h走势: :{color}[{signal_icon} {change:.2f}%]")
            
            # --- 📈 画图 ---
            st.subheader(f"{signal_icon} {selected_coin} 价格走势")
            c = alt.Chart(df_coin).mark_line(point=True).encode(
                x=alt.X('时间', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('价格', scale=alt.Scale(zero=False)),
                tooltip=['时间', '价格']
            ).interactive()
            st.altair_chart(c, use_container_width=True)

            # ================= 🤖 AI 分析核心区域 =================
            st.divider()
            st.subheader(f"🤖 AI 智能分析 ({selected_coin})")

            # 创建一个大按钮
            if st.button(f"✨ 让 AI 分析 {selected_coin} 的走势"):
                
                # 1. 准备数据 (取最近 15 条)
                recent_data = df_coin.tail(15).to_string(index=False)
                
                # 2. 显示加载动画
                with st.spinner("AI 正在通过卫星连接华尔街大脑..."):
                    try:
                        # 3. 呼叫 AI
                        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "你是一个资深加密货币交易员，擅长技术分析。请根据用户提供的数据，分析价格趋势，识别支撑位和阻力位，并给出简短的操作建议（买入/卖出/观望）。语气要专业、犀利。"},
                                {"role": "user", "content": f"这是 {selected_coin} 最近的行情数据：\n{recent_data}"}
                            ],
                            stream=False
                        )
                        
                        # 4. 展示结果
                        analysis = response.choices[0].message.content
                        st.success("分析完成！")
                        st.markdown(f"### 📝 分析报告：\n{analysis}")
                        
                    except Exception as e:
                        st.error(f"AI 罢工了：{e}")
            # ====================================================

            with st.expander("查看原始数据"):
                st.dataframe(df_coin.sort_index(ascending=False))
        else:
            st.warning("暂无数据。")
    else:
        st.error("Excel 格式不对。")
else:
    st.warning("找不到数据文件。")