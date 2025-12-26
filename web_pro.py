import streamlit as st
import pandas as pd
import os
import altair as alt

st.set_page_config(page_title="Crypto Pro 看板", layout="wide")
st.title("🚀 全币种量化监控室")

file_path = "全币种监控表.xlsx"

if st.button("🔄 刷新数据"):
    st.rerun()

if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    
    # --- 🕹 交互区域 ---
    # 1. 获取 Excel 里所有的币种名字 (去重)
    coin_list = df["币种"].unique()
    
    # 2. 创建一个下拉菜单，让用户选
    selected_coin = st.selectbox("👉 请选择你要查看的币种:", coin_list)
    
    # --- 🧹 数据清洗 ---
    # 3. 关键步骤：只筛选出用户选中的那个币的数据！
    df_coin = df[df["币种"] == selected_coin]
    
    # 按时间排序
    df_coin = df_coin.sort_values(by="时间")

    # --- 📊 展示区域 (和之前一样，但数据变成了筛选后的 df_coin) ---
    latest_price = df_coin["价格"].iloc[-1]
    
    # 计算涨跌
    if len(df_coin) > 1:
        prev_price = df_coin["价格"].iloc[-2]
        change = (latest_price - prev_price) / prev_price * 100
        color = "green" if change > 0 else "red"
    else:
        change = 0
        color = "gray"

    col1, col2 = st.columns(2)
    col1.metric(f"{selected_coin} 价格", f"${latest_price:,.4f}", f"{change:.2f}%")
    
    # 画图
    st.subheader(f"📈 {selected_coin} 价格走势")
    
    # 使用 Altair 画动态图
    c = alt.Chart(df_coin).mark_line(point=True).encode(
        x=alt.X('时间', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('价格', scale=alt.Scale(zero=False)),
        tooltip=['时间', '价格']
    ).interactive()
    
    st.altair_chart(c, use_container_width=True)

else:
    st.error("请先运行 `crypto_pro.py` 生成数据！")