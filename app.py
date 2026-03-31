import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
import src.storage as storage
import src.database as database

# --- 1. ページ基本設定 ---
st.set_page_config(
    page_title="Arisa's T-Shirt Shop",
    page_icon="👕",
    layout="centered"
)

# --- 2. セッション状態の初期化 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "cart" not in st.session_state:
    st.session_state.cart = []

if "order_confirmed_step" not in st.session_state:
    st.session_state.order_confirmed_step = False

if "config" not in st.session_state:
    st.session_state.config = {
        "paypay_id": "arisa_tshirt",
        "bank_info": "〇〇銀行 △△支店 普通 1234567",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"
    }

# 商品マスタの初期化
if "items_master" not in st.session_state:
    with st.spinner("データを読み込み中..."):
        df = database.load_items()
        if df is not None and not df.empty:
            st.session_state.items_master = df
        else:
            st.session_state.items_master = pd.DataFrame(columns=["id", "category", "size", "price", "stock", "img"])

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
    items_df = st.session_state.items_master

    if items_df.empty:
        st.info("現在、準備中です。しばらくお待ちください。")
        return

    st.subheader("1. 商品を選んでカートに追加")
    categories = items_df['category'].unique()
    selected_cat = st.selectbox("種類で絞り込む", categories)
    filtered_items = items_df[items_df['category'] == selected_cat]
    
    cols = st.columns(len(filtered_items) if len(filtered_items) > 0 else 1)
    for i, (_, row) in enumerate(filtered_items.iterrows()):
        with cols[i]:
            img_url = row['img'] if row['img'] else "https://via.placeholder.com/150?text=No+Image"
            st.image(img_url, use_container_width=True)
            st.write(f"**サイズ: {row['size']}**")
            st.write(f"¥{row['price']:,} (残り{row['stock']}枚)")
            
            quantity = st.number_input(
                "枚数", 
                min_value=1, 
                max_value=int(row['stock']) if row['stock'] > 0 else 1, 
                value=1, 
                key=f"qty_{row['id']}",
                disabled=(row['stock'] <= 0)
            )
            
            if st.button(f"カートに入れる", key=f"btn_{row['id']}", use_container_width=True):
                if row['stock'] >= quantity:
                    for _ in range(quantity):
                        st.session_state.cart.append({"id": row['id'], "name": f"{row['category']} ({row['size']})", "price": row['price']})
                    st.toast(f"{row['category']} を追加しました！")
                    st.rerun()
                else:
                    st.error("在庫切れです")

    st.divider()

    st.subheader("🛒 現在のカート内容")
    if not st.session_state.cart:
        st.write("カートは空です。")
        total_price = 0
    else:
        summary = {}
        for item in st.session_state.cart:
            item_id = item['id']
            if item_id not in summary:
                summary[item_id] = {"name": item['name'], "price": item['price'], "count": 0}
            summary[item_id]["count"] += 1
        
        total_price = 0
        for item_id, info in summary.items():
            c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 0.5])
            c1.write(f"**{info['name']}**")
            subtotal = info['price'] * info['count']
            c2.write(f"¥{subtotal:,}")
            
            if c3.button("ー", key=f"minus_{item_id}"):
                for i, item in enumerate(st.session_state.cart):
                    if item['id'] == item_id:
                        st.session_state.cart.pop(i)
                        break
                st.rerun()
            c4.write(f"{info['count']}枚")
            if c5.button("＋", key=f"plus_{item_id}"):
                master_row = st.session_state.items_master[st.session_state.items_master['id'] == item_id].iloc[0]
                if master_row['stock'] > info['count']:
                    st.session_state.cart.append({"id": item_id, "name": info['name'], "price": info['price']})
                    st.rerun()
                else:
                    st.error("在庫上限です")
            total_price += subtotal
        
        st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">合計金額: <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span></div>', unsafe_allow_html=True)

    if total_price > 0:
        st.subheader("2. お客様情報の入力")
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            user_name = st.text_input("お名前（フルネーム）")
            user_team = st.text_input("チーム名", placeholder="（例）ありさTシャツ部")
        with col_u2:
            user_tel = st.text_input("電話番号")
            transfer_name = st.text_input("お振込名義（カタカナ）", placeholder="（例）ヤマダ タロウ")
        
        pay_method = st.radio("支払い方法", ["PayPay", "銀行振込"])

        if not st.session_state.order_confirmed_step:
            if st.button("注文内容を確認する", use_container_width=True, type="primary"):
                if user_name and user_tel and transfer_name:
                    st.session_state.order_confirmed_step = True
                    st.rerun()
                else:
                    st.error("お名前、電話番号、お振込名義は必須入力です")
        else:
            st.markdown("""<div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border: 1px solid #ffeeba; margin-top: 20px;">
                    <h4 style="color: #856404; margin-top: 0;">💰 お支払いのご案内</h4></div>""", unsafe_allow_html=True)
            if pay_method == "PayPay":
                st.warning(f"【PayPay】ID: **{st.session_state.config['paypay_id']}** へ送金してください。")
                pay_ref = st.text_input("決済番号の下4桁（任意）")
            else:
                st.warning(f"【銀行振込】{st.session_state.config['bank_info']} へお振り込みください。")
                pay_ref = "銀行振込"
            st.write(f"**最終合計金額: ¥{total_price:,}**")
            has_paid = st.checkbox("支払いを完了しました（または後ほど必ず行います）")
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("入力し直す", use_container_width=True):
                st.session_state.order_confirmed_step = False
                st.rerun()
            if c_btn2.button("注文を確定する", use_container_width=True, type="primary"):
                with st.spinner("注文データを送信中..."):
                    order_items = ", ".join([f"{info['name']} x {info['count']}" for info in summary.values()])
                    order_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, user_team, user_tel, transfer_name, order_items, total_price, pay_method, pay_ref, "未対応"]
                    try:
                        database.add_order(order_data)
                        st.balloons(); st.success("注文完了！"); st.session_state.cart = []; st.session_state.order_confirmed_step = False
                        time.sleep(3); st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")

# --- 5. 管理者用：管理パネル ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    if not st.session_state.authenticated:
        pwd = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if pwd == st.secrets.get("admin_password", "admin123"):
                st.session_state.authenticated = True; st.rerun()
            else: st.error("パスワードが違います")
        return

    tab1, tab2, tab3 = st.tabs(["📊 受注管理", "📦 商品マスタ管理", "🔧 ショップ設定"])
    
    with tab1:
        st.subheader("注文一覧")
        if st.button("最新の注文を読み込む"):
            orders_df = database.load_orders()
            if orders_df is not None: st.dataframe(orders_df, use_container_width=True)

    with tab2:
        st.subheader("新商品の追加")
        with st.expander("＋ 商品を新規登録する"):
            new_cat = st.text_input("商品カテゴリ/名", placeholder="（例）ロゴTシャツ2026")
            new_price = st.number_input("価格", value=3500, step=100)
            size_list = ["S", "M", "L", "XL", "XXL"]
            selected_sizes = []
            size_cols = st.columns(len(size_list))
            for i, s in enumerate(size_list):
                if size_cols[i].checkbox(s, key=f"reg_s_{s}"):
                    selected_sizes.append(s)
            u_file = st.file_uploader("商品画像", type=["jpg", "png", "jpeg"])
            
            if st.button("この内容で登録（一時保存）"):
                if new_cat and selected_sizes:
                    with st.spinner("画像をアップロード中..."):
                        img_url = storage.upload_image(u_file)
                    current_df = st.session_state.items_master
                    current_max_id = current_df['id'].astype(int).max() if not current_df.empty else 0
                    new_rows = []
                    for i, s in enumerate(selected_sizes):
                        new_rows.append({"id": int(current_max_id + (i + 1)), "category": new_cat, "size": s, "price": new_price, "stock": 0, "img": img_url})
                    st.session_state.items_master = pd.concat([current_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.success("追加しました！下の「GSSに保存」ボタンで確定してください。")

        st.divider()
        st.subheader("在庫・価格の編集")
        edited_df = st.data_editor(
            st.session_state.items_master,
            column_config={"id": None, "price": st.column_config.NumberColumn("単価", format="¥%d"), "img": st.column_config.ImageColumn("画像リンク")},
            hide_index=True, use_container_width=True
        )
        if st.button("編集内容をGSSに保存", type="primary"):
            database.save_items(edited_df)
            st.session_state.items_master = edited_df
            st.success("マスターデータを更新しました")

    with tab3:
        st.subheader("ショップ設定")
        st.session_state.config['paypay_id'] = st.text_input("PayPay ID", value=st.session_state.config['paypay_id'])
        st.session_state.config['bank_info'] = st.text_area("銀行口座", value=st.session_state.config['bank_info'])
        if st.button("設定を保存"): st.success("保存しました")

if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()