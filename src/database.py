import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import os

# スプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    """Google Sheets APIに接続（決定版）"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # 1. ローカルファイルがある場合
        if os.path.exists('service_account.json'):
            creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        
        # 2. Streamlit CloudのSecretsを使う場合
        else:
            # Secretsから辞書として取得
            # .to_dict() がエラーになる場合があるため、dict() で変換
            raw_creds = st.secrets["gcp_service_account"]
            creds_dict = dict(raw_creds)
            
            # 秘密鍵の改行文字を本物の改行に変換
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 認証失敗: {e}")
        return None

def save_items(df):
    """商品マスタを保存する"""
    client = get_gss_client()
    # clientがNone（空）のまま進むと AttributeError になるのでここで止める
    if client is None:
        st.error("認証クライアントの作成に失敗したため、保存できません。")
        return

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        worksheet.clear()
        
        # DataFrameをリスト形式に変換して書き込み
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data)
        st.success("✅ スプレッドシートを更新しました！")
    except Exception as e:
        st.error(f"💾 保存エラー: {e}")
def load_orders():
    """受注データを読み込む"""
    client = get_gss_client()
    if client is None:
        return pd.DataFrame()

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        # 「orders」という名前のシート（タブ）を読みに行くよ
        worksheet = sh.worksheet("orders")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"注文データの読み込みエラー: {e}")
        # まだシートがない場合は、空のカラムだけ準備するよ
        return pd.DataFrame(columns=["日時", "お名前", "電話番号", "注文内容", "合計金額", "支払い方法", "決済番号", "対応ステータス"])