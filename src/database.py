def get_gss_client():
    """Google Sheets APIに接続（改行エラー対策版）"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        if os.path.exists('service_account.json'):
            creds = Credentials.from_service_account_file('service_account.json', scopes=scopes)
        else:
            # Streamlit CloudのSecretsから取得
            # .to_dict() をつけることで、扱いやすい辞書形式にするよ
            creds_info = st.secrets["gcp_service_account"].to_dict()
            
            # --- ここが最重要ポイント！ ---
            # 秘密鍵の中にある「\\n」（文字列としての改行）を、
            # 「\n」（本物の改行）に置き換える処理を追加するよ
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 認証に失敗しました: {e}")
        return None