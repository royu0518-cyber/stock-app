import streamlit as st
import pandas as pd
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

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

# スプレッドシート名＆シート名
SPREADSHEET_NAME = "stock-app"
WORKSHEET_NAME = "holdings"

sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


# =========================
# データ取得（重要：ここだけがデータ源）
# =========================
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)


# =========================
# 銘柄追加
# =========================
def add_row(row):
    sheet.append_row(row)


# =========================
# 追加フォーム（iPhone対応）
# =========================
st.subheader("➕ 銘柄追加")

with st.form("add_form"):
    name = st.text_input("会社名")
    ticker = st.text_input("ティッカー（例：7203.T）")
    shares = st.number_input("持ち株数", min_value=0)
    price = st.number_input("購入単価", min_value=0.0)

    submitted = st.form_submit_button("追加")

    if submitted:
        if name and ticker:
            add_row([name, ticker, shares, price])
            st.success("追加しました！")
        else:
            st.error("会社名とティッカーは必須です")


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

            market_value = latest * shares
            profit = (latest - cost) * shares
            day_change = (latest - prev) * shares
            day_rate = ((latest - prev) / prev) * 100

            rows.append({
                "会社名": row["会社名"],
                "ティッカー": ticker,
                "持ち株数": shares,
                "購入単価": cost,
                "最新株価": latest,
                "前日終値": prev,
                "評価額": market_value,
                "評価損益": profit,
                "当日変動率": day_rate,
                "当日評価変動額": day_change
            })

        except Exception:
            continue

    return pd.DataFrame(rows)


# =========================
# 更新ボタン
# =========================
if st.button("🔄 更新"):
    st.cache_data.clear()


# =========================
# 表示
# =========================
df = calc()

if df.empty:
    st.warning("データがありません")
    st.stop()

# サマリー
st.metric("総資産", f"{df['評価額'].sum():,.0f}円")
st.metric("評価損益", f"{df['評価損益'].sum():,.0f}円")

def color_profit(val):
    try:
        num = float(str(val).replace(",", ""))
        if num > 0:
            return "color: green"
        elif num < 0:
            return "color: red"
    except:
        pass
    return ""
    


# 表示用整形

display = df.copy()

for col in ["評価額", "評価損益", "当日評価変動額"]:
    display[col] = display[col].map(lambda x: f"{x:,.0f}")

display["当日変動率"] = display["当日変動率"].map(lambda x: f"{x:.2f}%")

styled = display[
[
"会社名",
"ティッカー",
"評価額",
"評価損益",
"当日変動率",
"当日評価変動額",
"持ち株数",
"購入単価",
"最新株価"
]
].style.map(
color_profit,
subset=["評価損益", "当日評価変動額"]
)

styled = styled.set_properties(
    subset=[
        "評価額",
        "評価損益",
        "当日変動率",
        "当日評価変動額",
        "持ち株数",
        "購入単価",
        "最新株価"
    ],
    **{"text-align": "right"}
)

styled = styled.set_table_styles([
    # 全体は右寄せ
    {"selector": "td", "props": [("text-align", "right")]},
    {"selector": "th", "props": [("text-align", "right")]},

    # 会社名だけ左寄せ
    {"selector": "td:nth-child(1)", "props": [("text-align", "left")]},
    {"selector": "th:nth-child(1)", "props": [("text-align", "left")]},

    # ティッカーだけ左寄せ
    {"selector": "td:nth-child(2)", "props": [("text-align", "left")]},
    {"selector": "th:nth-child(2)", "props": [("text-align", "left")]}
])

display = display.sort_values(by="評価額", ascending=False)

st.write(styled.to_html(), unsafe_allow_html=True)
