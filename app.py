import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="株管理", layout="wide")

st.title("📈 株管理")

@st.cache_data(ttl=300)
def load_data():
df = pd.read_csv("holdings.csv")
rows = []

for _, row in df.iterrows():
    try:
        ticker = row["ティッカー"]
        shares = float(row["持ち株数"])
        cost = float(row["購入単価"])

        hist = yf.Ticker(ticker).history(period="7d")

        if len(hist) < 2:
            continue

        latest = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])

        market_value = latest * shares
        profit = (latest - cost) * shares
        day_change = (latest - prev) * shares
        day_rate = ((latest - prev) / prev) * 100

        rows.append(
            {
                "会社名": row["会社名"],
                "評価額": market_value,
                "評価損益": profit,
                "当日変動率": day_rate,
                "当日評価変動額": day_change,
                "持ち株数": shares,
                "購入単価": cost,
                "前日終値": prev,
                "最新株価": latest,
                "ティッカー": ticker,
            }
        )

    except Exception:
        continue

return pd.DataFrame(rows)

if st.button("🔄 株価更新"):
st.cache_data.clear()

result = load_data()

if len(result) == 0:
st.error("データが取得できません")
st.stop()

total_value = result["評価額"].sum()
total_profit = result["評価損益"].sum()
total_day = result["当日評価変動額"].sum()

c1, c2, c3 = st.columns(3)

c1.metric("総資産", f"{total_value:,.0f}円")
c2.metric("評価損益", f"{total_profit:,.0f}円")
c3.metric("本日変動", f"{total_day:,.0f}円")

st.divider()

display = result.copy()

for col in ["評価額", "評価損益", "当日評価変動額"]:
display[col] = display[col].map(lambda x: f"{x:,.0f}")

display["当日変動率"] = display["当日変動率"].map(
lambda x: f"{x:.2f}%"
)

st.dataframe(
display[
[
"会社名",
"評価額",
"評価損益",
"当日変動率",
"当日評価変動額",
"持ち株数",
"購入単価",
"最新株価",
]
],
use_container_width=True,
hide_index=True,
)
