import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import os

# スプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    """Google Sheets APIに接続（1行Secrets・改行コード完全対応版）"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # 1. ローカルのJSONファイルがある場合（テスト用）
        if os.path.exists('service_account.json'):
            creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        
        # 2. Streamlit CloudのSecretsを使う場合
        else:
            # Secretsの中にキーが存在するかチェック
            if "gcp_service_account" not in st.secrets:
                st.error("❌ Secretsの中に 'gcp_service_account' が見つかりません。")
                return None
            
            # 辞書として取得
            creds_dict = dict(st.secrets["gcp_service_account"])
            
            # 秘密鍵の処理：1行で書かれていても対応する
            if "private_key" in creds_dict:
                pk = creds_dict["private_key"]
                # エスケープされた改行を本物に変換
                pk = pk.replace("\\n", "\n")
                # 前後の余計な引用符を除去
                pk = pk.strip('"').strip("'")
                creds_dict["private_key"] = pk
            
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 認証エラー: {e}")
        return None

def load_items():
    """商品マスタを読み込む"""
    client = get_gss_client()
    if client is None: return pd.DataFrame()
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"商品データ読み込みエラー: {e}")
        return pd.DataFrame(columns=["id", "category", "size", "price", "stock", "img"])

def load_orders():
    """受注データを読み込む"""
    client = get_gss_client()
    if client is None: return pd.DataFrame()
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("orders")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"注文データ読み込みエラー: {e}")
        return pd.DataFrame(columns=["日時", "お名前", "電話番号", "注文内容", "合計金額", "支払い方法", "決済番号", "対応ステータス"])

def save_items(df):
    """商品マスタを保存する"""
    client = get_gss_client()
    if client is None: return
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        worksheet.clear()
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data)
        st.success("✅ スプレッドシートを更新しました！")
    except Exception as e:
        st.error(f"💾 保存エラー: {e}")

def add_order(order_data):
    """新しい注文を追記する"""
    client = get_gss_client()
    if client is None: return
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("orders")
        worksheet.append_row(order_data)
    except Exception as e:
        st.error(f"🛒 注文記録エラー: {e}")