import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# のんちゃんが用意してくれたスプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    """Google Sheets APIに接続するためのクライアントを作成"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # JSONファイルが同じフォルダにあることを確認してね
        creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        # 鍵が見つからない、または認証に失敗した場合
        st.error(f"認証エラー: {e}")
        return None

def load_items():
    """商品マスタを読み込む"""
    client = get_gss_client()
    if client is None:
        return pd.DataFrame() # 認証失敗時は空のデータを返す

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items") # 「items」という名前のシートを探す
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame()

def save_items(df):
    """商品マスタを全上書き保存する"""
    client = get_gss_client()
    if client is None:
        return

    sh = client.open_by_url(SPREADSHEET_URL)
    worksheet = sh.worksheet("items")
    worksheet.clear()
    # ヘッダーを含めてデータを流し込む
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

def add_order(order_data):
    """新しい注文を受注管理シートに追記する"""
    client = get_gss_client()
    if client is None:
        return

    sh = client.open_by_url(SPREADSHEET_URL)
    worksheet = sh.worksheet("orders") # 「orders」という名前のシートを探す
    worksheet.append_row(order_data)