import io
import numpy as np
from PIL import Image

def image_to_text(uploaded_file):
    try:
        from paddleocr import PaddleOCR
        # 注意：这里不要再传 show_log 参数
        ocr = PaddleOCR(lang="ch", use_textline_orientation=True,enable_mkldnn=False)
        
        image_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        if len(image_np.shape) == 3 and image_np.shape[2] == 4:
            image_np = image_np[:, :, :3]
            
        # --- 使用 3.x 的 predict 方法 ---
        results = ocr.predict(image_np)
        
        text = ""
        if results:
            for res in results:
                # 从字典的 rec_texts 键中提取文字
                if 'rec_texts' in res:
                    for item in res['rec_texts']:
                        text += item + "\n"
                            
        print(f"====== 最终提取的文本：\n{text} ======")
        return text

    except Exception as e:
        print(f"❌ OCR识别出错: {e}")
        return ""