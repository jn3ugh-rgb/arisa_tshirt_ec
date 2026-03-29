import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. ページ基本設定 & UIカスタム ---
st.set_page_config(
    page_title="Official T-Shirt Order System",
    page_icon="👕",
    layout="centered"
)

# カスタムCSSの読み込み（リッチなUI用）
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("assets/css/style.css")

# --- 2. ナビゲーション（サイドバー） ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("表示画面を選択", ["注文フォーム", "管理者パネル"])

# --- 3. ユーザー用：注文フォーム画面 ---
def show_order_form():
    st.markdown('<h1 class="main-title">Official T-Shirt Order</h1>', unsafe_allow_html=True)
    st.write("ご希望のTシャツを選択し、必要事項を入力してください。")

    # 本来はDB(inventory)から取得するが、MVP用にダミーデータを定義
    # SKU: [商品名, サイズ, 単価, 在庫数]
    items_master = {
        "BLACK-L": ["Tシャツ（黒）", "L", 3500, 15],
        "WHITE-M": ["Tシャツ（白）", "M", 3500, 10],
        "ADV-S": ["アドバンス", "S", 4000, 5]
    }

    st.subheader("1. 商品を選択")
    order_quantities = {}
    
    # 3列で商品を表示
    cols = st.columns(len(items_master))
    for i, (sku, info) in enumerate(items_master.items()):
        with cols[i]:
            st.image("https://via.placeholder.com/150", caption=f"{info[0]} ({info[1]})")
            st.write(f"価格: ¥{info[2]:,}")
            st.write(f"在庫: {info[3]}")
            order_quantities[sku] = st.number_input("数量", min_value=0, max_value=info[3], step=1, key=sku)

    # 合計金額の計算
    total_price = sum(order_quantities[sku] * items_master[sku][2] for sku in items_master)

    if total_price > 0:
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
                <span style="font-size: 18px; color: #555;">ご注文合計金額</span><br>
                <span style="font-size: 32px; font-weight: bold; color: #ff4b4b;">¥{total_price:,}</span>
                <p style="font-size: 12px; color: #888; margin-top: 5px;">※振込手数料はご負担ください</p>
            </div>
        """, unsafe_allow_html=True)

    # 注文者情報
    st.subheader("2. お届け先・ご連絡先")
    with st.container():
        order_type = st.selectbox("注文区分", ["個人", "チーム代表者"])
        team_name = st.text_input("所属チーム名（個人の場合は空欄）")
        user_name = st.text_input("お名前（代表者氏名）")
        tel = st.text_input("電話番号")
        transfer_name = st.text_input("振込名義（カタカナ）", help="消込に使用します")

    # 決済方法
    st.subheader("3. お支払い方法")
    pay_method = st.radio("支払い方法を選択", ["PayPay", "銀行振込"])

    if st.button("内容を確認して注文する", use_container_width=True):
        if not user_name or not tel:
            st.error("お名前と電話番号を入力してください。")
        elif total_price == 0:
            st.warning("商品を選択してください。")
        else:
            order_id = datetime.now().strftime("%y%m%d%H%M")
            st.balloons()
            st.success(f"注文を受け付けました！注文ID: {order_id}")
            
            if pay_method == "PayPay":
                st.info("以下のQRコードから送金をお願いします。")
                st.image("assets/images/paypay_qr.png", width=200)
                st.warning("送金後、決済番号の末尾4桁を公式LINEへお送りください。")
            else:
                st.info("以下の口座へお振込みをお願いします。")
                st.code(f"振込名義：{order_id} {transfer_name}\n〇〇銀行 △△支店 普通 1234567")

# --- 4. 管理者用：管理パネル ---
def show_admin_panel():
    st.title("⚙️ 管理者専用パネル")
    
    # 簡易パスワード認証
    pwd = st.text_input("管理者パスワードを入力", type="password")
    if pwd != st.secrets.get("admin_password", "admin123"):
        st.error("パスワードが正しくありません")
        return

    # タブの修正（AttributeError対策）
    tab1, tab2, tab3 = st.tabs(["受注一覧", "在庫・商品管理", "設定"])
    
    with tab1:
        st.subheader("受注データ一覧")
        # ダミーデータ
        dummy_orders = pd.DataFrame({
            "注文ID": ["26033001", "26033002"],
            "名前": ["米山望", "ありさ"],
            "金額": [3500, 7000],
            "状態": ["未入金", "入金済"]
        })
        st.dataframe(dummy_orders, use_container_width=True)
        st.button("選択した注文を入金済みに更新")

    with tab2:
        st.subheader("📦 商品マスタ・在庫管理")
        st.write("商品の追加や在庫数の変更ができます。")
        
        # 簡易的な在庫編集フォーム
        with st.expander("＋ 新規商品を登録する"):
            new_sku = st.text_input("SKUコード (例: BLACK-XL)")
            new_name = st.text_input("商品名")
            new_price = st.number_input("単価", min_value=0, step=100)
            if st.button("商品を登録"):
                st.toast(f"商品 {new_name} を登録しました（未実装）")

        st.divider()
        st.write("現在の在庫一覧（編集可能）")
        # 本来はDBから読み込んだものを st.data_editor で表示
        inventory_data = pd.DataFrame([
            {"SKU": "BLACK-L", "商品名": "Tシャツ（黒）", "在庫": 15},
            {"SKU": "WHITE-M", "商品名": "Tシャツ（白）", "在庫": 10}
        ])
        st.data_editor(inventory_data, num_rows="dynamic")
        st.button("在庫情報を一括保存")

    with tab3:
        st.subheader("基本設定")
        st.text_input("振込先銀行口座情報", value="〇〇銀行 △△支店 普通 1234567")
        st.file_uploader("PayPay QRコード画像を更新", type=["png", "jpg"])
        st.button("設定を保存")

# --- 5. メインルーティング ---
if app_mode == "注文フォーム":
    show_order_form()
else:
    show_admin_panel()