import io
from PIL import Image
import base64

def upload_image(uploaded_file):
    """
    画像をリサイズし、本番はGCS URLを、テスト時はBase64データURLを返す。
    """
    if uploaded_file is None:
        # 画像がない場合はプレースホルダーを返す
        return "https://via.placeholder.com/150?text=No+Image"

    try:
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
        # 元のフォーマットを維持（なければJPEG）
        format_str = img.format if img.format else "JPEG"
        img.save(img_batch, format=format_str, quality=85)
        img_data = img_batch.getvalue()
        
        # --- 本番環境用のロジック (コメントアウト中) ---
        # ここで GCS にアップロードし、その公開URLを return する
        # url = gcs_upload_function(img_data, uploaded_file.name)
        # return url

        # --- テスト環境用：Base64エンコードして直接表示可能な形式にする ---
        # これならサーバーに保存しなくても、ブラウザが画像として認識してくれるよ！
        base64_encoded = base64.b64encode(img_data).decode("utf-8")
        return f"data:image/{format_str.lower()};base64,{base64_encoded}"

    except Exception as e:
        print(f"Error processing image: {e}")
        return "https://via.placeholder.com/150?text=Error"