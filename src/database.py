import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# スプレッドシートのURL（のんちゃんがくれたもの）
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1IEnzTaI5Yqbkc9H4jmv3D4DfjWrUdbh21tzXWSwTyjQ/edit"

def get_gss_client():
    # 本来は Streamlit Secrets から読み込む
    # scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    # return gspread.authorize(creds)
    pass

def load_items():
    """商品マスタを読み込む"""
    try:
        client = get_gss_client()
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("items")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except:
        # シートがない場合などのフォールバック
        return pd.DataFrame(columns=["id", "category", "size", "price", "stock", "img"])

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