import io
from PIL import Image
# from google.cloud import storage # 本番環境でGCSを使う場合

def upload_image(uploaded_file):
    """画像をリサイズして保存し、URLを返す"""
    if uploaded_file is None:
        return "https://via.placeholder.com/150"

    # 1. 画像を開く
    img = Image.open(uploaded_file)
    
    # 2. リサイズ処理 (アスペクト比維持、最大幅800px)
    max_width = 800
    if img.width > max_width:
        ratio = max_width / float(img.width)
        height = int(float(img.height) * float(ratio))
        img = img.resize((max_width, height), Image.Resampling.LANCZOS)
    
    # 3. メモリ上のバッファに保存
    img_batch = io.BytesIO()
    # 元の形式を維持しつつ、JPEGなら画質調整
    img_format = img.format if img.format else "JPEG"
    img.save(img_batch, format=img_format, quality=85)
    img_batch.seek(0)
    
    # --- テスト用の擬似処理 ---
    # 本来はここで GCS にアップロードして公開URLを取得する
    # 今回はテスト用に「仮想のURL」を返す形にするね
    test_url = f"https://storage.googleapis.com/arisa-bucket/resized_{uploaded_file.name}"
    
    return test_url