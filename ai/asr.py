import os
import tempfile
import whisper


# =========================================================
# 1. FFmpeg 配置
# =========================================================

# 注意：
# 这里填写的是 ffmpeg.exe 所在的“文件夹”
# 不是 ffmpeg.exe 文件本身
FFMPEG_DIR = r"D:\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin"


if os.path.exists(FFMPEG_DIR):
    os.environ["PATH"] = (
        FFMPEG_DIR
        + os.pathsep
        + os.environ.get("PATH", "")
    )


# =========================================================
# 2. 加载 Whisper 模型
# =========================================================

print("正在加载 Whisper 模型，请稍等...")

model = whisper.load_model("base")

print("Whisper 模型加载完成")


# =========================================================
# 3. 语音识别
# =========================================================

def speech_to_text(uploaded_file):
    """
    Django 上传文件
    ↓
    临时保存
    ↓
    Whisper
    ↓
    返回中文文本
    """

    if uploaded_file is None:
        raise ValueError("没有收到录音文件")

    # 获取原始文件扩展名
    original_name = uploaded_file.name

    suffix = os.path.splitext(original_name)[1].lower()

    # 没有扩展名时，默认 wav
    if not suffix:
        suffix = ".wav"

    # 支持的格式
    allowed_formats = {
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".ogg",
        ".webm",
        ".aac",
    }

    if suffix not in allowed_formats:
        raise ValueError(
            f"暂不支持 {suffix} 格式，请上传 MP3、WAV、M4A、FLAC、OGG 或 WebM。"
        )

    temp_path = None

    try:

        # =================================================
        # 保存临时录音
        # =================================================

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        ) as temp_file:

            temp_path = temp_file.name

            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

        print("录音临时文件：", temp_path)
        print("录音格式：", suffix)

        # =================================================
        # Whisper 识别
        # =================================================

        result = model.transcribe(
            temp_path,

            # 中文
            language="zh",

            # CPU环境更加稳定
            fp16=False,

            # 初始提示词
            initial_prompt=(
                "这是一段中文课堂、学习或人工智能相关的录音。"
                "请尽可能准确识别专业术语。"
            )
        )

        text = result.get("text", "").strip()

        if not text:
            raise ValueError(
                "录音没有识别出有效文字，请检查录音是否有声音。"
            )

        print("识别结果：")
        print(text)

        return text

    except Exception as e:

        print("================================")
        print("Whisper 语音识别失败")
        print("错误：", repr(e))
        print("================================")

        raise RuntimeError(
            f"语音识别失败：{str(e)}"
        )

    finally:

        # =================================================
        # 删除临时文件
        # =================================================

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)

            except Exception:
                pass