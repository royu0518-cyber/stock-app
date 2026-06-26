import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# =========================
# 設定
# =========================
st.set_page_config(page_title="株管理", layout="wide")
st.title("📈 株管理")

# =========================
# Google Sheets 接続
# =========================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

SPREADSHEET_NAME = "stock-app"
WORKSHEET_NAME = "holdings"


def get_sheet():
    return client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


# =========================
# データ取得
# =========================
def load_data():
    sheet = get_sheet()
    return pd.DataFrame(sheet.get_all_records())


# =========================
# 追加
# =========================
def add_row(row):
    sheet = get_sheet()
    sheet.append_row(row)


# =========================
# 削除（完全修正版）
# =========================
def delete_row_by_ticker(ticker):
    try:
        sheet = get_sheet()

        cell = sheet.find(str(ticker))
        sheet.delete_row(cell.row)

    except Exception as e:
        st.error(f"削除エラー: {e}")


# =========================
# 株価計算
# =========================
@st.cache_data(ttl=300)
def calc():
    df = load_data()
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
                "ティッカー": ticker,
                "持ち株数": shares,
                "購入単価": cost,
                "最新株価": latest,
                "前日終値": prev,
                "評価額": latest * shares,
                "評価損益": (latest - cost) * shares,
                "当日変動率": ((latest - prev) / prev) * 100,
                "当日評価変動額": (latest - prev) * shares
            })

        except:
            continue

    return pd.DataFrame(rows)


# =========================
# データ取得（1回だけ）
# =========================
df = calc()

if df.empty:
    st.warning("データがありません")
    st.stop()

# =========================
# サマリー（最上部）
# =========================
st.metric("総資産", f"{df['評価額'].sum():,.0f}円")
st.metric("評価損益", f"{df['評価損益'].sum():,.0f}円")

st.divider()

# =========================
# 一覧表示
# =========================
st.subheader("📋 保有一覧")

for _, row in df.iterrows():

    col1, col2, col3, col4, col5 = st.columns([3,2,2,2,1])

    with col1:
        st.write(row["会社名"])

    with col2:
        st.write(row["ティッカー"])

    with col3:
        st.write(f"{row['評価額']:,.0f}円")

    with col4:
        st.write(f"{row['評価損益']:,.0f}円")

    with col5:
        if st.button("🗑", key=row["ティッカー"]):
            delete_row_by_ticker(row["ティッカー"])
            st.cache_data.clear()
            st.rerun()

st.divider()

# =========================
# 追加フォーム
# =========================
st.subheader("➕ 銘柄追加")

with st.form("add_form"):
    name = st.text_input("会社名")
    ticker = st.text_input("ティッカー（例：7203.T）")
    shares = st.number_input("持ち株数", min_value=0.0)
    price = st.number_input("購入単価", min_value=0.0)

    submitted = st.form_submit_button("追加")

    if submitted:
        if name and ticker:
            add_row([name, ticker, shares, price])
            st.success("追加しました！")
            st.rerun()
        else:
            st.error("会社名とティッカーは必須です")

# =========================
# 更新ボタン
# =========================
if st.button("🔄 更新"):
    st.cache_data.clear()
    st.rerun()
