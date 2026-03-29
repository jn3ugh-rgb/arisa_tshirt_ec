import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. ページ基本設定 & リッチUI用CSS ---
st.set_page_config(
    page_title="Official T-Shirt Order",
    page_icon="👕",
    layout="centered"
)

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# CSSの読み込み（assets/css/style.css がある想定）
local_css("assets/css/style.css")

# --- 2. モード切り替え（サイドバー） ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("表示画面を選択", ["注文フォーム", "管理者パネル"])

# --- 3. ユーザー用：注文フォーム画面 ---
def show_order_form():
    st.markdown('<h1 class="main-title">Official T-Shirt Order</h1>', unsafe_allow_html=True)
    
    # 1. 単価の設定（本来はinventoryシートから取得）
    PRICE_BLACK = 3500
    PRICE_WHITE = 3500
    PRICE_ADVANCE = 4000

    st.subheader("1. 商品を選択")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://via.placeholder.com/150", caption=f"Black (¥{PRICE_BLACK:,})")
        q_black = st.number_input("数量", min_value=0, step=1, key="q_black")
    with col2:
        st.image("https://via.placeholder.com/150", caption=f"White (¥{PRICE_WHITE:,})")
        q_white = st.number_input("数量", min_value=0, step=1, key="q_white")
    with col3:
        st.image("https://via.placeholder.com/150", caption=f"Advance (¥{PRICE_ADVANCE:,})")
        q_adv = st.number_input("数量", min_value=0, step=1, key="q_adv")

    # 2. 合計金額の計算
    total_price = (q_black * PRICE_BLACK) + (q_white * PRICE_WHITE) + (q_adv * PRICE_ADVANCE)

    # 3. 合計金額のリッチな表示
    if total_price > 0:
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <span style="font-size: 18px; color: #555;">ご注文合計金額</span><br>
                <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
            </div>
        """, unsafe_allow_html=True)
    
    # --- このあとにユーザー情報入力や決済選択を続ける ---
    # 注文者情報
    st.subheader("2. お届け先・ご連絡先")
    with st.container():
        order_type = st.selectbox("注文区分", ["個人", "チーム代表者"])
        team_name = st.text_input("所属チーム名（個人の場合は空欄）")
        user_name = st.text_input("お名前（代表者氏名）")
        tel = st.text_input("電話番号")

    # 決済方法の選択
    st.subheader("3. お支払い方法")
    pay_method = st.radio("支払い方法を選択", ["PayPay", "銀行振込"])

    if st.button("内容を確認して注文する", use_container_width=True):
        # ここでバリデーションとID生成を行う
        order_id = datetime.now().strftime("%y%m%d%H%M")
        
        # セッションに入力内容を保持して「決済案内画面」へ（簡易実装）
        st.success(f"注文を受け付けました！注文ID: {order_id}")
        
        if pay_method == "PayPay":
            st.info("以下のQRコードから送金をお願いします。")
            st.image("assets/images/paypay_qr.png", width=200)
            st.warning("送金後、決済番号の末尾4桁を公式LINEへお送りください。")
        else:
            st.info("以下の口座へお振込みをお願いします。")
            st.code(f"振込名義：{order_id} {user_name}\n〇〇銀行 △△支店 普通 1234567")

# --- 4. 管理者用：管理パネル ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    
    # 簡易パスワード認証
    pwd = st.text_input("管理者パスワードを入力", type="password")
    if pwd != st.secrets.get("admin_password", "admin123"):
        st.error("パスワードが正しくありません")
        return

    tab1, tab2, tab3 = st.tabs(["受注一覧", "在庫管理", "設定"])
    
    with tab1:
        st.subheader("未入金の注文")
        # 本来はGSheetsから読み込んだDataFrameを表示
        dummy_data = pd.DataFrame({
            "ID": ["24032901", "24032902"],
            "名前": ["山田太郎", "佐藤花子"],
            "金額": [3500, 7000],
            "状態": ["未入金", "未入金"]
        })
        st.dataframe(dummy_data, use_container_width=True)
        
        if st.button("選択した注文を入金済みにする"):
            st.toast("入金ステータスを更新しました！")

    with tab2:
        st.subheader("現在の在庫数")
        # 在庫編集フォーム
        st.number_input("Black Lサイズ 在庫", value=15)
        st.button("在庫を更新する")

# --- 5. メインルーティング ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()