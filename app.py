# =========================
# 表示（UI）
# =========================
st.subheader("📋 保有一覧")

df = calc()

if df.empty:
    st.warning("データがありません")
    st.stop()

# =========================
# カード型一覧（削除ボタン付き）
# =========================
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
# 📊 表形式（詳細テーブル）
# =========================
st.subheader("📊 詳細テーブル")

display = df.copy()

# ソート
display = display.sort_values(by="評価額", ascending=False)
display = display.reset_index(drop=True)
display.insert(0, "NO", display.index + 1)

# 購入からの変動率
display["購入からの変動率"] = (
    (display["最新株価"] - display["購入単価"])
    / display["購入単価"] * 100
)

# 表示用フォーマット
display["評価額"] = display["評価額"].map(lambda x: f"{x:,.0f}")
display["評価損益"] = display["評価損益"].map(lambda x: f"{x:,.0f}")
display["当日評価変動額"] = display["当日評価変動額"].map(lambda x: f"{x:,.0f}")

display["当日変動率"] = display["当日変動率"].map(lambda x: f"{x:.2f}%")
display["購入からの変動率"] = display["購入からの変動率"].map(lambda x: f"{x:.2f}%")

# 表示列
styled = display[
    [
        "NO",
        "会社名",
        "ティッカー",
        "評価額",
        "評価損益",
        "当日変動率",
        "購入からの変動率",
        "持ち株数",
        "購入単価",
        "最新株価"
    ]
]

st.dataframe(styled, use_container_width=True)

# =========================
# 追加フォーム
# =========================
st.divider()

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
