import streamlit as st
import pandas as pd
import yfinance as yf
import os

st.set_page_config(page_title="株管理", layout="wide")
st.title("📈 株管理")

FILE = "holdings.csv"


# CSV読み込み
def load_csv():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    else:
        return pd.DataFrame(columns=["会社名", "ティッカー", "持ち株数", "購入単価"])


# CSV保存
def save_csv(df):
    df.to_csv(FILE, index=False)


# 追加フォーム
st.subheader("➕ 銘柄追加")

with st.form("add_form"):
    name = st.text_input("会社名")
    ticker = st.text_input("ティッカー（例：7203.T）")
    shares = st.number_input("持ち株数", min_value=0)
    price = st.number_input("購入単価", min_value=0.0)

    submitted = st.form_submit_button("追加")

    if submitted:
        df = load_csv()
        new_row = pd.DataFrame([[name, ticker, shares, price]],
                               columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df)
        st.success("追加しました！リロードしてください")


# 株価計算
@st.cache_data(ttl=300)
def calc():
    df = load_csv()
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

            rows.append({
                "会社名": row["会社名"],
                "評価額": latest * shares,
                "評価損益": (latest - cost) * shares,
                "当日変動率": ((latest - prev) / prev) * 100,
                "当日評価変動額": (latest - prev) * shares,
                "持ち株数": shares,
                "購入単価": cost,
                "最新株価": latest,
                "ティッカー": ticker
            })

        except:
            continue

    return pd.DataFrame(rows)


if st.button("🔄 更新"):
    st.cache_data.clear()

df = calc()

if len(df) == 0:
    st.warning("データなし")
    st.stop()

st.metric("総資産", f"{df['評価額'].sum():,.0f}円")
st.metric("評価損益", f"{df['評価損益'].sum():,.0f}円")

st.dataframe(df, use_container_width=True)
