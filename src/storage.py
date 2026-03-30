import io
from PIL import Image
# from google.cloud import storage # 本番環境でGCSを使う場合

def upload_image(uploaded_file):
    """
    画像をバックグラウンドでリサイズ・最適化し、テスト用のダミーURLを返す。
    """
    if uploaded_file is None:
        return "https://via.placeholder.com/150?text=No+Image"

    try:
        # 1. バックグラウンドで画像処理開始
        # アップロードされたファイルを開く
        img = Image.open(uploaded_file)
        
        # 2. 【可変（リサイズ）】
        # アスペクト比を維持しつつ、最大幅を800pxに制限する
        max_width = 800
        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int(float(img.height) * float(ratio))
            # 高品質なリサイズを行う（スクショの文字も潰れにくい）
            img = img.resize((max_width, height), Image.Resampling.LANCZOS)
        
        # アルファチャンネル（透明度）がある場合は、JPEGに変換するために背景を白にする
        if img.mode in ('RGBA', 'LA'):
            background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
            background.paste(img, img.get_all_pixels())
            img = background.convert('RGB')
        
        # 3. 【最適化（軽量化）】
        # メモリ上のバッファに保存し、JPEG形式、画質85%で圧縮する
        img_batch = io.BytesIO()
        img.save(img_batch, format="JPEG", quality=85)
        img_data = img_batch.getvalue() # これがリサイズ済みのデータ

        # --- 重要：ここが「テスト環境」のポイント！ ---
        # この『img_data』はスプレッドシートに入れない！
        # 本番環境ではここでGCSにアップロードし、そのURL（短い文字列）をreturnする。
        #今はテストなので、短いダミーURLを返す。
        test_url = f"https://via.placeholder.com/150?text={uploaded_file.name}_Resized"
        
        return test_url

    except Exception as e:
        # エラーが起きた場合は、エラー画像を返す
        print(f"Error processing image: {e}")
        return "https://via.placeholder.com/150?text=Error"