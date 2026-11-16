import re
import jieba

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF


# =========================================================
# 停用词
# =========================================================

STOP_WORDS = {
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "然后",
    "就是",
    "可以",
    "一个",
    "一些",
    "以及",
    "因为",
    "所以",
    "但是",
    "如果",
    "进行",
    "通过",
    "关于",
    "其中",
    "目前",
    "其实",
    "比较",
    "非常",
    "老师",
    "同学",
}


# =========================================================
# 文本清洗
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text)

    # 去掉网址
    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    # 去掉多余符号
    text = re.sub(
        r"[^\u4e00-\u9fa5a-zA-Z0-9]",
        " ",
        text
    )

    # jieba 分词
    words = jieba.lcut(text)

    result = []

    for word in words:

        word = word.strip()

        if not word:
            continue

        if word in STOP_WORDS:
            continue

        if len(word) < 2:
            continue

        result.append(word)

    return " ".join(result)


# =========================================================
# 关键词提取
# =========================================================

def extract_keywords(text, top_k=10):

    cleaned = clean_text(text)

    if not cleaned:
        return []

    words = cleaned.split()

    counter = {}

    for word in words:
        counter[word] = counter.get(word, 0) + 1

    sorted_words = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        word
        for word, count in sorted_words[:top_k]
    ]


# =========================================================
# NMF主题分析
# =========================================================

def topic_analysis(texts):

    if not texts:
        return {
            "topics": [],
            "keywords": [],
            "summary": ""
        }

    # -----------------------------------------------------
    # 合并文本
    # -----------------------------------------------------

    original_text = "\n".join(
        [str(x) for x in texts if x]
    )

    if not original_text.strip():
        return {
            "topics": [],
            "keywords": [],
            "summary": ""
        }

    # -----------------------------------------------------
    # 如果只有一段文本
    # -----------------------------------------------------

    if len(texts) == 1:

        keywords = extract_keywords(
            original_text,
            top_k=10
        )

        return {
            "topics": [
                {
                    "name": "主要内容",
                    "keywords": keywords
                }
            ],

            "keywords": keywords,

            "summary": original_text[:300]
        }

    # -----------------------------------------------------
    # 中文分词
    # -----------------------------------------------------

    cleaned_texts = [
        clean_text(text)
        for text in texts
        if text
    ]

    cleaned_texts = [
        text
        for text in cleaned_texts
        if text.strip()
    ]

    if not cleaned_texts:

        return {
            "topics": [],
            "keywords": [],
            "summary": ""
        }

    # -----------------------------------------------------
    # TF-IDF
    # -----------------------------------------------------

    vectorizer = TfidfVectorizer(
        max_features=1000,

        # 中文已经经过 jieba 分词
        token_pattern=r"(?u)\b\w+\b",

        min_df=1
    )

    try:

        matrix = vectorizer.fit_transform(
            cleaned_texts
        )

    except ValueError:

        keywords = extract_keywords(
            original_text
        )

        return {
            "topics": [
                {
                    "name": "主要内容",
                    "keywords": keywords
                }
            ],
            "keywords": keywords,
            "summary": original_text[:300]
        }

    # -----------------------------------------------------
    # NMF主题数量
    # -----------------------------------------------------

    n_topics = min(
        3,
        matrix.shape[0],
        matrix.shape[1]
    )

    if n_topics < 1:

        keywords = extract_keywords(
            original_text
        )

        return {
            "topics": [
                {
                    "name": "主要内容",
                    "keywords": keywords
                }
            ],
            "keywords": keywords,
            "summary": original_text[:300]
        }

    # -----------------------------------------------------
    # NMF
    # -----------------------------------------------------

    nmf = NMF(
        n_components=n_topics,
        random_state=42,
        init="nndsvda",
        max_iter=500
    )

    nmf.fit_transform(matrix)

    feature_names = vectorizer.get_feature_names_out()

    topics = []

    all_keywords = []

    for index, component in enumerate(
        nmf.components_
    ):

        top_indices = component.argsort()[
            ::-1
        ][:8]

        keywords = [
            feature_names[i]
            for i in top_indices
        ]

        all_keywords.extend(
            keywords
        )

        topics.append(
            {
                "name": f"主题 {index + 1}",
                "keywords": keywords
            }
        )

    # 去重
    all_keywords = list(
        dict.fromkeys(all_keywords)
    )

    return {
        "topics": topics,

        "keywords": all_keywords[:15],

        "summary": original_text[:500]
    }