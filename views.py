import re
from django.shortcuts import render
from django.http import HttpResponse
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from openai import OpenAI

# 导入你自己的模块
from .ai.asr import speech_to_text
from .ai.ocr import image_to_text

# 👇 核心魔法：直接导入本地保险柜里的 Key！
from .secret_key import DEEPSEEK_KEY

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

def home(request):
    return render(request, 'home.html')

def _format_run(run):
    """统一字体：微软雅黑、11号、绝对不加粗"""
    run.font.name = 'Arial'
    run.font.size = Pt(11)
    run.bold = False
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def generate_doc(request):
    if request.method == 'POST':
        raw_text = request.POST.get('user_input', '') or ''
        image = request.FILES.get('image')
        audio = request.FILES.get('audio')
        
        all_text = []
        if raw_text.strip():
            all_text.append(raw_text)
            
        if audio:
            try:
                asr_text = speech_to_text(audio)
                if asr_text:
                    all_text.append(f"\n【语音识别内容如下】：\n{asr_text}")
            except Exception as e:
                all_text.append(f'[音频转写失败: {e}]')
                
        if image:
            try:
                ocr_text = image_to_text(image)
                if ocr_text:
                    all_text.append(f"\n【图片识别内容如下】：\n{ocr_text}")
            except Exception as e:
                all_text.append(f'[图片识别失败: {e}]')

        if not any(t.strip() for t in all_text):
            return HttpResponse('❌ 文本、录音和图片不能同时为空！', status=400)

        combined_text = '\n'.join(t for t in all_text if t.strip())

        prompt = f"""
        你是一位资深的大学教授和知识科普专家。请根据我提供的原始内容，进行深度分析、提炼和引申。
        我的目的是让学生或听众能够轻易理解这些知识，所以请你不要简单地罗列原文，而是要加入你的解释。
        
        具体要求如下：
        1. 提取核心概念，用通俗易懂的语言进行解释。
        2. 必须包含“引申与拓展”部分，举例说明这些知识在实际生活或工作中的用途。
        3. 使用清晰的多级标题结构（例如：一、核心概念；1. 知识点）。
        4. 【绝对指令】：直接输出纯文本，禁止使用任何 Markdown 符号（如 *、#），不要任何加粗、倾斜！
        
        原始内容如下：
        {combined_text}
        """

        try:
            # 直接使用导入的 Key
            client = OpenAI(api_key=DEEPSEEK_KEY, base_url=DEEPSEEK_BASE_URL)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            ai_result = response.choices[0].message.content or ''
        except Exception as e:
            return HttpResponse(f"❌ AI接口报错: {str(e)}", status=500)

        # 清洗数据
        clean_text = re.sub(r'[*#`_]', '', ai_result)

        # 生成绝对统一排版的 Word
        document = Document()
        for line in clean_text.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
                
            paragraph = document.add_paragraph()
            run = paragraph.add_run(stripped)
            _format_run(run) 
            paragraph.paragraph_format.space_after = Pt(6)

        http_response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        http_response['Content-Disposition'] = 'attachment; filename="AI整理笔记.docx"'
        document.save(http_response)
        return http_response

    return render(request, 'home.html')