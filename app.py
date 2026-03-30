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

# ダミーの商品マスタ（本来は db.get_inventory() から取得）
if "items_master" not in st.session_state:
    st.session_state.items_master = pd.DataFrame([
        {"id": 1, "category": "Tシャツ（黒）", "size": "S", "price": 3500, "stock": 5, "img": "https://via.placeholder.com/150"},
        {"id": 2, "category": "Tシャツ（黒）", "size": "L", "price": 3500, "stock": 10, "img": "https://via.placeholder.com/150"},
        {"id": 3, "category": "Tシャツ（白）", "size": "M", "price": 3500, "stock": 8, "img": "https://via.placeholder.com/150"},
    ])

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

    st.subheader("1. 商品を選んでカートに追加")
    categories = items_df['category'].unique()
    selected_cat = st.selectbox("種類で絞り込む", categories)
    
    filtered_items = items_df[items_df['category'] == selected_cat]
    
    cols = st.columns(len(filtered_items))
    for i, (_, row) in enumerate(filtered_items.iterrows()):
        with cols[i]:
            st.image(row['img'], use_container_width=True)
            st.write(f"**サイズ: {row['size']}**")
            st.write(f"¥{row['price']:,} (残り{row['stock']}枚)")
            
            if st.button(f"カートに入れる", key=f"btn_{row['id']}"):
                if row['stock'] > 0:
                    st.session_state.cart.append({
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
        total_price = 0
        for idx, item in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(item['name'])
            c2.write(f"¥{item['price']:,}")
            if c3.button("削除", key=f"del_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()
            total_price += item['price']
        
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <span style="font-size: 18px; color: #555;">ご注文合計金額</span><br>
                <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
            </div>
        """, unsafe_allow_html=True)

    if total_price > 0:
        st.subheader("2. お客様情報の入力")
        user_name = st.text_input("お名前")
        user_tel = st.text_input("電話番号")
        
        st.subheader("3. お支払い方法")
        pay_method = st.radio("支払い方法を選択", ["PayPay", "銀行振込"])
        
        if pay_method == "PayPay":
            pp_id = st.session_state.config['paypay_id']
            st.info(f"PayPay ID: **{pp_id}** を検索して送金してください。")
            st.code(pp_id, language=None)
            paypay_ref = st.text_input("決済番号の下4桁")
        
        if st.button("注文を確定する", use_container_width=True):
            if user_name and user_tel:
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
        return

    tab1, tab2, tab3 = st.tabs(["📊 受注管理", "📦 商品マスタ管理", "🔧 ショップ設定"])
    
    with tab1:
        st.subheader("注文一覧")
        st.info("ここにスプレッドシートの注文データが表示されます")

    with tab2:
        st.subheader("新商品の追加（サイズ一括登録）")
        with st.expander("＋ 種類ごとにまとめて登録する"):
            new_cat = st.text_input("商品名（例：2026限定Tシャツ）")
            new_price = st.number_input("価格", value=3500, step=100)
            
            st.write("展開するサイズを選択：")
            size_list = ["S", "M", "L", "XL", "XXL"]
            selected_sizes = []
            size_cols = st.columns(len(size_list))
            for i, s in enumerate(size_list):
                if size_cols[i].checkbox(s, key=f"reg_s_{s}"):
                    selected_sizes.append(s)
            
            u_file = st.file_uploader("商品画像（共通）", type=["jpg", "png"])
            
            if st.button("この内容で一括登録"):
                if new_cat and selected_sizes:
                    # 1. 新しいデータのリストを作成
                    new_rows = []
                    for s in selected_sizes:
                        new_id = len(st.session_state.items_master) + 1
                        new_rows.append({
                            "id": new_id,
                            "category": new_cat,
                            "size": s,
                            "price": new_price,
                            "stock": 0,  # 初期在庫は0
                            "img": "https://via.placeholder.com/150" # 仮画像
                        })
                    
                    # 2. 既存のDataFrameに結合
                    new_df = pd.DataFrame(new_rows)
                    st.session_state.items_master = pd.concat(
                        [st.session_state.items_master, new_df], 
                        ignore_index=True
                    )
                    
                    st.success(f"「{new_cat}」を登録しました！")
                    
                    # 3. 重要：画面を再描画して表を更新する
                    st.rerun()
                else:
                    st.warning("商品名とサイズを選んでください")

        st.divider()
        st.subheader("商品データの一覧")
        st.write("※金額や在庫を直接書き換えて「保存」を押してください。")
        
        # st.data_editor を使った一括編集
        edited_df = st.data_editor(
            st.session_state.items_master,
            column_config={
                "price": st.column_config.NumberColumn("単価", format="¥%d"),
                "stock": st.column_config.NumberColumn("在庫数"),
                "img": st.column_config.ImageColumn("画像URL")
            },
            disabled=["id"],
            hide_index=True,
            use_container_width=True
        )
        st.divider()
        st.subheader("🗑️ 商品の削除")
        
        # 削除対象を選ぶためのリストを作成（ID - カテゴリ - サイズ）
        delete_options = [
            f"{row['id']}: {row['category']} ({row['size']})" 
            for _, row in st.session_state.items_master.iterrows()
        ]
        
        target_to_delete = st.multiselect(
            "削除する商品を選択してください（複数可）", 
            options=delete_options
        )
        
        if st.button("選択した商品を完全に削除する", type="primary"):
            if target_to_delete:
                # 選択された文字列から「ID」だけを取り出す
                ids_to_drop = [int(item.split(":")[0]) for item in target_to_delete]
                
                # 指定したID以外を残す（フィルタリング）
                st.session_state.items_master = st.session_state.items_master[
                    ~st.session_state.items_master['id'].isin(ids_to_drop)
                ]
                
                st.success(f"{len(ids_to_drop)} 件の商品を削除しました。")
                st.rerun()
            else:
                st.warning("削除する商品を選んでください。")

        if st.button("編集内容をマスタに保存"):
            st.session_state.items_master = edited_df
            # db.update_inventory(edited_df)
            st.success("商品情報を更新しました！")

    with tab3:
        st.subheader("ショップ基本設定")
        st.session_state.config['paypay_id'] = st.text_input("PayPay ID", value=st.session_state.config['paypay_id'])
        st.session_state.config['bank_info'] = st.text_area("銀行口座情報", value=st.session_state.config['bank_info'])
        if st.button("設定内容を保存"):
            st.success("基本設定を保存しました")

# --- 6. メイン実行 ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()