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

# 設定情報の管理
if "config" not in st.session_state:
    st.session_state.config = {
        "paypay_id": "arisa_tshirt",
        "bank_info": "〇〇銀行 △△支店 普通 1234567",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"
    }

# 【修正】商品マスタの初期化（二重チェックを回避）
if "items_master" not in st.session_state:
    with st.spinner("スプレッドシートから最新データを読み込み中..."):
        df = database.load_items()
        # 読み込みに成功し、データが存在する場合
        if df is not None and not df.empty:
            st.session_state.items_master = df
        else:
            # 失敗、または空の場合は空のDataFrameを準備（カラム定義を正確に）
            st.session_state.items_master = pd.DataFrame(columns=["id", "category", "size", "price", "stock", "img"])
            if df is None:
                st.error("スプレッドシートへの接続に失敗しました。Secretsの設定を確認してください。")

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
        st.info("現在、商品情報を準備中です。ありささんにお問い合わせください。")
        return

    st.subheader("1. 商品を選んでカートに追加")
    
    # カテゴリがある場合のみ表示
    categories = items_df['category'].unique() if not items_df.empty else []
    if len(categories) > 0:
        selected_cat = st.selectbox("種類で絞り込む", categories)
        filtered_items = items_df[items_df['category'] == selected_cat]
        
        # 商品を横並びで表示
        cols = st.columns(len(filtered_items) if len(filtered_items) > 0 else 1)
        for i, (_, row) in enumerate(filtered_items.iterrows()):
            with cols[i]:
                # 画像がない場合のプレースホルダー対応
                img_path = row['img'] if row['img'] else "https://via.placeholder.com/150?text=No+Image"
                st.image(img_path, use_container_width=True)
                st.write(f"**{row['size']} サイズ**")
                st.write(f"¥{row['price']:,} (残り{row['stock']}枚)")
                
                if st.button(f"カートに入れる", key=f"btn_{row['id']}"):
                    if row['stock'] > 0:
                        st.session_state.cart.append({
                            "id": row['id'],
                            "name": f"{row['category']} ({row['size']})",
                            "price": row['price']
                        })
                        st.toast(f"🛒 {row['category']} をカートに追加！")
                        st.rerun()
                    else:
                        st.error("在庫切れです")
    
    st.divider()

    st.subheader("🛒 現在のカート内容")
    if not st.session_state.cart:
        st.write("カートは空です。")
        total_price = 0
    else:
        total_price = 0
        for idx, item in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(item['name'])
            c2.write(f"¥{item['price']:,}")
            if c3.button("削除", key=f"del_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()
            total_price += item['price']
        
        st.markdown(f'''
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                合計金額: <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
            </div>
        ''', unsafe_allow_html=True)

    if total_price > 0:
        st.subheader("2. お客様情報の入力")
        user_name = st.text_input("お名前（フルネーム）")
        user_tel = st.text_input("連絡先（電話番号）")
        pay_method = st.radio("支払い方法", ["PayPay", "銀行振込"])
        
        pay_ref = ""
        if pay_method == "PayPay":
            st.info(f"PayPay ID: **{st.session_state.config['paypay_id']}** へ送金後、番号を入力してください。")
            pay_ref = st.text_input("決済番号の下4桁")
        
        if st.button("注文を確定する", use_container_width=True, type="primary"):
            if user_name and user_tel:
                with st.spinner("注文を記録中..."):
                    order_items = ", ".join([item['name'] for item in st.session_state.cart])
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
                    st.success("注文が完了しました！ありささんへ連絡してくださいね。")
                    st.session_state.cart = []
            else:
                st.error("お名前と電話番号を入力してください。")

# --- 5. 管理者用：管理パネル ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    
    if not st.session_state.authenticated:
        pwd = st.text_input("パスワードを入力", type="password")
        if st.button("ログイン"):
            # Secretsにパスワードがない場合のデフォルトを設定
            admin_pwd = st.secrets.get("admin_password", "admin123")
            if pwd == admin_pwd:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
        return

    tab1, tab2, tab3 = st.tabs(["📊 受注管理", "📦 商品管理", "🔧 設定"])
    
    with tab1:
        st.subheader("注文一覧")
        if st.button("最新の注文を読み込む"):
            orders_df = database.load_orders()
            if orders_df is not None:
                st.dataframe(orders_df, use_container_width=True)
            else:
                st.error("注文データの読み込みに失敗しました。")

    with tab2:
        st.subheader("商品の追加・更新")
        with st.expander("＋ 新しい商品を登録する"):
            new_cat = st.text_input("商品シリーズ名（例：ArisaロゴT）")
            new_price = st.number_input("販売価格", value=3500, step=100)
            size_list = ["S", "M", "L", "XL", "XXL"]
            selected_sizes = []
            size_cols = st.columns(len(size_list))
            for i, s in enumerate(size_list):
                if size_cols[i].checkbox(s, key=f"reg_s_{s}"):
                    selected_sizes.append(s)
            
            u_file = st.file_uploader("商品画像をアップロード", type=["jpg", "png", "jpeg"])
            
            if st.button("この内容で追加する"):
                if new_cat and selected_sizes:
                    with st.spinner("画像を最適化中..."):
                        img_url = storage.upload_image(u_file)
                    
                    # 現在のIDの最大値を取得して、新しいIDを割り振る
                    current_df = st.session_state.items_master
                    current_max_id = current_df['id'].max() if not current_df.empty else 0
                    
                    new_rows = []
                    for i, s in enumerate(selected_sizes):
                        new_rows.append({
                            "id": int(current_max_id + (i + 1)),
                            "category": new_cat,
                            "size": s,
                            "price": new_price,
                            "stock": 0,
                            "img": img_url
                        })
                    
                    st.session_state.items_master = pd.concat([current_df, pd.DataFrame(new_rows)], ignore_index=True)
                    st.success("追加しました！下の「変更を保存」ボタンでGSSに反映させてください。")
                else:
                    st.warning("商品名とサイズを選択してください。")

        st.divider()
        
        # エディタでの編集
        st.subheader("在庫・価格の一括編集")
        edited_df = st.data_editor(
            st.session_state.items_master,
            column_config={
                "id": None, # IDは非表示
                "price": st.column_config.NumberColumn("単価", format="¥%d"),
                "stock": st.column_config.NumberColumn("在庫数"),
                "img": st.column_config.ImageColumn("商品画像")
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("変更を保存してGSSに反映", type="primary"):
            if edited_df is not None:
                with st.spinner("スプレッドシートを更新中..."):
                    # database.pyのsave_itemsを呼び出す
                    database.save_items(edited_df)
                    st.session_state.items_master = edited_df
            else:
                st.error("データが空です。")

        st.divider()
        st.subheader("🗑️ 商品の削除")
        if not st.session_state.items_master.empty:
            delete_options = [f"{row['id']}: {row['category']} ({row['size']})" for _, row in st.session_state.items_master.iterrows()]
            target_to_delete = st.multiselect("削除する商品（複数選択可）", options=delete_options)
            if st.button("選択した商品を完全に削除", type="secondary"):
                if target_to_delete:
                    ids_to_drop = [int(item.split(":")[0]) for item in target_to_delete]
                    new_df = st.session_state.items_master[~st.session_state.items_master['id'].isin(ids_to_drop)]
                    database.save_items(new_df)
                    st.session_state.items_master = new_df
                    st.success("削除が完了しました！")
                    st.rerun()

    with tab3:
        st.subheader("ショップ基本情報の設定")
        st.session_state.config['sheet_url'] = st.text_input("スプレッドシートURL", value=st.session_state.config['sheet_url'])
        st.session_state.config['paypay_id'] = st.text_input("PayPay ID", value=st.session_state.config['paypay_id'])
        st.session_state.config['bank_info'] = st.text_area("振込先口座情報", value=st.session_state.config['bank_info'])
        if st.button("設定を一時保存"):
            st.success("現在のセッションに設定を保存しました。")

# --- 6. メイン処理 ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()