import streamlit as st
import pandas as pd
from datetime import datetime
import os
# import src.database as db
# import src.storage as storage

# --- 1. ページ基本設定 ---
st.set_page_config(
    page_title="Arisa's T-Shirt Shop",
    page_icon="🛒",
    layout="centered"
)

# --- 2. セッション状態の初期化 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "cart" not in st.session_state:
    st.session_state.cart = []

if "config" not in st.session_state:
    st.session_state.config = {
        "paypay_id": "arisa_tshirt",
        "bank_info": "〇〇銀行 △△支店 普通 1234567"
    }

# --- 3. ナビゲーション ---
st.sidebar.title("Shop Menu")
app_mode = st.sidebar.radio("画面切り替え", ["注文フォーム", "管理者パネル"])

if st.session_state.authenticated:
    st.sidebar.divider()
    if st.sidebar.button("管理者ログアウト"):
        st.session_state.authenticated = False
        st.rerun()

# --- 4. ユーザー用：注文フォーム画面 ---
def show_order_form():
    st.markdown('# 👕 Official T-Shirt Order')
    
    # 【商品データ】本来は db.get_inventory() 
    items_master = pd.DataFrame([
        {"id": 1, "category": "Tシャツ（黒）", "size": "S", "price": 3500, "stock": 5, "img": "https://via.placeholder.com/150"},
        {"id": 2, "category": "Tシャツ（黒）", "size": "L", "price": 3500, "stock": 10, "img": "https://via.placeholder.com/150"},
        {"id": 3, "category": "Tシャツ（白）", "size": "M", "price": 3500, "stock": 8, "img": "https://via.placeholder.com/150"},
    ])

    # --- 商品選択エリア ---
    st.subheader("1. 商品を選んでカートに追加")
    
    # 種類で絞り込み
    categories = items_master['category'].unique()
    selected_cat = st.selectbox("種類で絞り込む", categories)
    
    filtered_items = items_master[items_master['category'] == selected_cat]
    
    # 商品を横並びで表示
    cols = st.columns(len(filtered_items))
    for i, (_, row) in enumerate(filtered_items.iterrows()):
        with cols[i]:
            st.image(row['img'], use_container_width=True)
            st.write(f"**サイズ: {row['size']}**")
            st.write(f"¥{row['price']:,} (残り{row['stock']}枚)")
            
            if st.button(f"カートに入れる", key=f"btn_{row['id']}"):
                if row['stock'] > 0:
                    st.session_state.cart.append({
                        "id": row['id'],
                        "name": f"{row['category']} ({row['size']})",
                        "price": row['price']
                    })
                    st.toast(f"{row['category']} を追加しました！")
                    st.rerun()
                else:
                    st.error("在庫がありません")

    st.divider()

    # --- カートの中身表示エリア ---
    st.subheader("🛒 現在のカート内容")
    
    if not st.session_state.cart:
        st.write("カートは空です。上のリストから商品を選んでください。")
        total_price = 0
    else:
        # カートの中身を整理
        total_price = 0
        for idx, item in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.write(item['name'])
            with c2:
                st.write(f"¥{item['price']:,}")
            with c3:
                if st.button("削除", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
            total_price += item['price']
        
        if st.button("カートを空にする"):
            st.session_state.cart = []
            st.rerun()

        # 合計金額の表示
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <span style="font-size: 18px; color: #555;">ご注文合計金額</span><br>
                <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
            </div>
        """, unsafe_allow_html=True)

    # --- 注文手続きエリア ---
    if total_price > 0:
        st.subheader("2. お客様情報の入力")
        user_name = st.text_input("お名前")
        user_tel = st.text_input("電話番号")
        
        st.subheader("3. お支払い方法")
        pay_method = st.radio("支払い方法を選択", ["PayPay", "銀行振込"])
        
        if pay_method == "PayPay":
            pp_id = st.session_state.config['paypay_id']
            st.info("以下のIDをコピーしてPayPayで送金してください。")
            st.code(pp_id, language=None)
            st.write(f"合計 **¥{total_price:,}** を送金後、決済番号の下4桁を入力してください。")
            paypay_ref = st.text_input("決済番号の下4桁")
        
        if st.button("注文を確定する", use_container_width=True):
            if user_name and user_tel:
                order_id = datetime.now().strftime("%y%m%d%H%M")
                st.balloons()
                st.success(f"注文完了！【注文ID: {order_id}】")
                st.session_state.cart = [] # カートを空にする
            else:
                st.error("お名前と電話番号を入力してください。")

# --- 5. 管理者用：管理パネル ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    
    if not st.session_state.authenticated:
        pwd = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if pwd == st.secrets.get("admin_password", "admin123"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("不正なパスワードです")
        return

    tab1, tab2, tab3 = st.tabs(["受注管理", "在庫・商品管理", "ショップ設定"])
    
    with tab1:
        st.subheader("注文一覧")
        st.write("※ここに注文データが表示されます")

    with tab2:
        st.subheader("商品マスタ管理")
        with st.expander("＋ 新規商品を登録"):
            n_cat = st.text_input("種類")
            n_size = st.selectbox("サイズ", ["S", "M", "L", "XL"])
            n_price = st.number_input("価格", value=3500)
            u_file = st.file_uploader("商品画像", type=["jpg", "png"])
            if st.button("登録"):
                st.success("商品をマスタに追加しました（MVP用メッセージ）")

    with tab3:
        st.subheader("基本設定")
        st.session_state.config['paypay_id'] = st.text_input("PayPay ID", value=st.session_state.config['paypay_id'])
        st.session_state.config['bank_info'] = st.text_area("銀行口座情報", value=st.session_state.config['bank_info'])
        if st.button("設定を保存"):
            st.success("設定を更新しました")

# --- 6. メイン実行 ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()