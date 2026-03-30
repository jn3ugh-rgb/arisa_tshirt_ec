import streamlit as st
import pandas as pd
from datetime import datetime
import os
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
            if df is None:
                st.error("スプレッドシートに接続できません。Secretsを確認してください。")

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
            
            # 枚数選択
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
                        st.session_state.cart.append({
                            "id": row['id'],
                            "name": f"{row['category']} ({row['size']})",
                            "price": row['price']
                        })
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
        # カートの中身を集計
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
            
            # 1枚減らす
            if c3.button("ー", key=f"minus_{item_id}"):
                for i, item in enumerate(st.session_state.cart):
                    if item['id'] == item_id:
                        st.session_state.cart.pop(i)
                        break
                st.rerun()

            c4.write(f"{info['count']}枚")

            # 1枚増やす
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
        user_name = st.text_input("お名前")
        user_tel = st.text_input("電話番号")
        pay_method = st.radio("支払い方法", ["PayPay", "銀行振込"])
        
        pay_ref = ""
        if pay_method == "PayPay":
            st.info(f"PayPay ID: **{st.session_state.config['paypay_id']}**")
            pay_ref = st.text_input("決済番号の下4桁")
        
        if st.button("注文を確定する", use_container_width=True, type="primary"):
            if user_name and user_tel:
                with st.spinner("注文を送信中..."):
                    order_items = ", ".join([f"{info['name']} x {info['count']}" for info in summary.values()])
                    order_data = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        user_name,
                        user_tel,
                        order_items,
                        total_price,
                        pay_method,
                        pay_ref,
                        "未対応"
                    ]
                    database.add_order(order_data)
                    st.balloons()
                    st.success("注文が完了しました！")
                    st.session_state.cart = []
            else:
                st.error("入力漏れがあります")

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
                st.error("パスワードが違います")
        return

    tab1, tab2, tab3 = st.tabs(["📊 受注管理", "📦 商品マスタ管理", "🔧 ショップ設定"])
    
    with tab1:
        st.subheader("注文一覧")
        if st.button("最新の注文を読み込む"):
            orders_df = database.load_orders()
            if orders_df is not None:
                st.dataframe(orders_df, use_container_width=True)
            else:
                st.error("注文データの読み込みに失敗しました。")

    with tab2:
        st.subheader("新商品の追加")
        with st.expander("＋ 商品を登録する"):
            new_cat = st.text_input("商品名")
            new_price = st.number_input("価格", value=3500, step=100)
            size_list = ["S", "M", "L", "XL", "XXL"]
            selected_sizes = []
            size_cols = st.columns(len(size_list))
            for i, s in enumerate(size_list):
                if size_cols[i].checkbox(s, key=f"reg_s_{s}"):
                    selected_sizes.append(s)
            
            u_file = st.file_uploader("商品画像", type=["jpg", "png", "jpeg"])
            
            if st.button("一括登録"):
                if new_cat and selected_sizes:
                    with st.spinner("画像を処理中..."):
                        img_url = storage.upload_image(u_file)
                    
                    current_df = st.session_state.items_master
                    current_max_id = current_df['id'].max() if not current_df.empty else 0
                    new_rows = []
                    for i, s in enumerate(selected_sizes):
                        new_rows.append({"id": int(current_max_id + (i + 1)), "category": new_cat, "size": s, "price": new_price, "stock": 0, "img": img_url})
                    
                    st.session_state.items_master = pd.concat([current_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.success("追加しました！下の保存ボタンを押してください。")

        st.divider()
        st.subheader("在庫・価格の編集")
        edited_df = st.data_editor(
            st.session_state.items_master,
            column_config={
                "id": None,
                "price": st.column_config.NumberColumn("単価", format="¥%d"),
                "img": st.column_config.ImageColumn("画像")
            },
            hide_index=True, use_container_width=True
        )
        
        if st.button("編集内容をGSSに保存", type="primary"):
            if edited_df is not None:
                with st.spinner("GSSを更新中..."):
                    database.save_items(edited_df)
                    st.session_state.items_master = edited_df

        st.divider()
        st.subheader("🗑️ 商品の削除")
        if not st.session_state.items_master.empty:
            delete_options = [f"{row['id']}: {row['category']} ({row['size']})" for _, row in st.session_state.items_master.iterrows()]
            target_to_delete = st.multiselect("削除する商品を選択", options=delete_options)
            if st.button("選択削除"):
                if target_to_delete:
                    ids_to_drop = [int(item.split(":")[0]) for item in target_to_delete]
                    new_df = st.session_state.items_master[~st.session_state.items_master['id'].isin(ids_to_drop)]
                    database.save_items(new_df)
                    st.session_state.items_master = new_df
                    st.rerun()

    with tab3:
        st.subheader("ショップ設定")
        st.session_state.config['paypay_id'] = st.text_input("PayPay ID", value=st.session_state.config['paypay_id'])
        st.session_state.config['bank_info'] = st.text_area("銀行口座", value=st.session_state.config['bank_info'])
        if st.button("設定を保存"):
            st.success("保存しました")

if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()