import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st # Streamlitのsecretsを使うために追加

# スプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    """Google Sheets APIに接続するためのクライアントを作成"""
    # 認証に必要な権限（スコープ）
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # --- 重要：認証情報の読み込み ---
    # ローカルテスト時はJSONファイル、本番はst.secretsを使うのが一般的だよ
    # 一旦、ローカルのJSONファイルを使う場合の書き方にするね
    try:
        # 'service_account.json' はのんちゃんがDLした鍵ファイルの名前に合わせてね
        creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"認証エラーが発生しました: {e}")
        return None
def save_items(df):
    """商品マスタを全上書き保存する"""
    client = get_gss_client()
    sh = client.open_by_url(SPREADSHEET_URL)
    worksheet = sh.worksheet("items")
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

def add_order(order_data):
    """新しい注文を受注管理シートに追記する"""
    client = get_gss_client()
    sh = client.open_by_url(SPREADSHEET_URL)
    worksheet = sh.worksheet("orders")
    worksheet.append_row(order_data)