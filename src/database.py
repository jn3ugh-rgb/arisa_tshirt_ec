import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import os

# スプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    """Google Sheets APIに接続するためのクライアントを作成"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # ファイルの場所を確認
    json_path = 'service_account.json'
    
    if not os.path.exists(json_path):
        st.error(f"⚠️ エラー: '{json_path}' が見つかりません。現在のフォルダ: {os.getcwd()}")
        return None
    
    try:
        creds = Credentials.from_service_account_file(json_path, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 認証に失敗しました: {e}")
        return None

def load_items():
    """商品マスタを読み込む"""
    client = get_gss_client()
    if client is None:
        return pd.DataFrame()

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"📝 シート読み込みエラー: {e}")
        # シート名が「items」になっているか確認してね
        return pd.DataFrame()

def save_items(df):
    """商品マスタを全上書き保存する"""
    client = get_gss_client()
    if client is None:
        st.error("認証に失敗しているため、保存できません。")
        return

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("スプレッドシートを更新しました！")
    except Exception as e:
        st.error(f"💾 保存エラー: {e}")

def add_order(order_data):
    """新しい注文を受注管理シートに追記する"""
    client = get_gss_client()
    if client is None:
        return

    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("orders")
        worksheet.append_row(order_data)
    except Exception as e:
        st.error(f"🛒 注文記録エラー: {e}")