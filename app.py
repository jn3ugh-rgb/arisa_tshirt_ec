import streamlit as st
import pandas as pd
from datetime import datetime
import os
# ※ 以下のモジュールは後ほど実装・接続する前提
# import src.database as db
# import src.storage as storage

# --- 1. ページ基本設定 ---
st.set_page_config(
    page_title="Arisa's T-Shirt Shop",
    page_icon="👕",
    layout="centered"
)

# --- 2. セッション状態（ログイン保持・設定値）の初期化 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 本来はDBから読み込む設定値（MVP用の初期値）
if "config" not in st.session_state:
    st.session_state.config = {
        "paypay_id": "arisa_tshirt",
        "bank_info": "〇〇銀行 △△支店 普通 1234567"
    }

# --- 3. ナビゲーション ---
st.sidebar.title("Shop Menu")
app_mode = st.sidebar.radio("画面を切り替える", ["注文フォーム", "管理者パネル"])

# ログイン済みの場合のみログアウトボタンを表示
if st.session_state.authenticated:
    st.sidebar.divider()
    if st.sidebar.button("管理者ログアウト"):
        st.session_state.authenticated = False
        st.toast("ログアウトしました")
        st.rerun()

# --- 4. ユーザー用：注文フォーム画面 ---
def show_order_form():
    st.markdown('# 👕 Official T-Shirt Order')
    st.write("ご希望の商品とサイズを選んでください。")
    
    # 【商品データ】本来は db.get_inventory() で取得
    items_master = pd.DataFrame([
        {"category": "Tシャツ（黒）", "size": "S", "price": 3500, "stock": 5, "img": "https://via.placeholder.com/150"},
        {"category": "Tシャツ（黒）", "size": "L", "price": 3500, "stock": 10, "img": "https://via.placeholder.com/150"},
        {"category": "Tシャツ（白）", "size": "M", "price": 3500, "stock": 8, "img": "https://via.placeholder.com/150"},
    ])

    st.subheader("1. 商品を選択")
    
    # 種類（Category）を選択
    categories = items_master['category'].unique()
    selected_cat = st.selectbox("種類を選んでね", categories)
    
    # 選択された種類に紐づくサイズ（Size）を表示
    filtered_df = items_master[items_master['category'] == selected_cat]
    selected_size = st.select_slider("サイズを選んでね", options=filtered_df['size'].tolist())
    
    # 選択された商品の詳細情報を特定
    item_info = filtered_df[filtered_df['size'] == selected_size].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(item_info['img'], width=150, caption=f"{selected_cat}")
    with col2:
        st.write(f"### 価格: ¥{item_info['price']:,}")
        st.write(f"在庫状況: 残り {item_info['stock']} 枚")
        quantity = st.number_input("数量を入力", min_value=0, max_value=item_info['stock'], step=1)

    total_price = item_info['price'] * quantity

    # 合計金額の表示
    if total_price > 0:
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <span style="font-size: 18px; color: #555;">ご注文合計金額</span><br>
                <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
                <p style="font-size: 12px; color: #888; margin-top: 5px;">※振込手数料はご負担ください</p>
            </div>
        """, unsafe_allow_html=True)

    # お支払い方法の案内
    if total_price > 0:
        st.subheader("2. お支払い方法")
        pay_method = st.radio("支払い方法を選択", ["PayPay", "銀行振込"])
        
        if pay_method == "PayPay":
            # 管理者画面で設定されたIDを反映
            pp_id = st.session_state.config['paypay_id']
            st.info("以下のIDをコピーしてPayPayアプリで送金してください。")
            st.code(pp_id, language=None)
            st.markdown(f"""
            **【送金の手順】**
            1. 上のIDをコピーします。
            2. PayPayアプリの「送る」→「PayPay IDで検索」に貼り付け。
            3. 金額 **¥{total_price:,}** を入力して送金。
            4. 完了画面の **[決済番号 下4桁]** を以下に入力。
            """)
            paypay_ref = st.text_input("PayPay決済番号の下4桁", placeholder="例：1234")
        
        else:
            # 管理者画面で設定された銀行情報を反映
            bank_info = st.session_state.config['bank_info']
            st.info("以下の口座へお振込みをお願いします。")
            st.code(bank_info)
            st.write("※振込名義の前に「注文ID（後ほど発行）」を付けていただけると確認がスムーズです。")

        if st.button("注文を確定する", use_container_width=True):
            order_id = datetime.now().strftime("%y%m%d%H%M")
            st.balloons()
            st.success(f"注文を受け付けました！【注文ID: {order_id}】")
            st.write("ありささんからの入金確認連絡をお待ちください。")

# --- 5. 管理者用：管理パネル画面 ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    
    # ログイン認証
    if not st.session_state.authenticated:
        pwd = st.text_input("管理者パスワードを入力してください", type="password")
        if st.button("ログイン"):
            if pwd == st.secrets.get("admin_password", "admin123"):
                st.session_state.authenticated = True
                st.toast("ログインしました！お疲れ様です、ありささん。")
                st.rerun()
            else:
                st.error("パスワードが正しくありません")
        return

    # ログイン後のメインコンテンツ
    tab1, tab2, tab3 = st.tabs(["📊 受注一覧", "📦 商品・在庫管理", "🔧 ショップ設定"])
    
    with tab1:
        st.subheader("現在の受注データ")
        # 受注一覧の表示（MVP用ダミー）
        st.info("※ここにスプレッドシートから読み込んだ注文リストが表示されます。")
    
    with tab2:
        st.subheader("商品の新規登録・在庫更新")
        
        with st.expander("＋ 新しい商品を追加する"):
            new_cat = st.text_input("種類（例：Tシャツ 黒）")
            new_size = st.selectbox("サイズ", ["S", "M", "L", "XL"])
            new_price = st.number_input("価格", min_value=0, step=100, value=3500)
            # 画像アップロード（後に storage.py でリサイズ処理を呼ぶ）
            uploaded_file = st.file_uploader("商品画像をアップロード", type=["jpg", "png"])
            
            if st.button("商品を登録実行"):
                # if uploaded_file:
                #     img_url = storage.upload_image(uploaded_file) # リサイズ＆アップロード
                #     db.add_item(new_cat, new_size, new_price, img_url)
                st.success(f"{new_cat} ({new_size}) をマスタに追加しました！")

        st.divider()
        st.write("既存商品の在庫数変更")
        # st.data_editor(db.get_inventory()) などの実装箇所
    
    with tab3:
        st.subheader("基本情報の設定")
        st.write("ユーザー画面に表示される支払い先情報を変更できます。")
        
        # PayPay IDの設定
        new_paypay_id = st.text_input(
            "PayPay ID（ユーザー画面にコピー用として表示されます）", 
            value=st.session_state.config['paypay_id']
        )
        
        # 銀行口座情報の設定
        new_bank_info = st.text_area(
            "銀行振込先情報", 
            value=st.session_state.config['bank_info']
        )
        
        if st.button("設定内容を保存"):
            st.session_state.config['paypay_id'] = new_paypay_id
            st.session_state.config['bank_info'] = new_bank_info
            # db.update_config(new_paypay_id, new_bank_info)
            st.success("ショップ設定を更新しました！ユーザー画面に即時反映されます。")

# --- 6. メインルーティング ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()