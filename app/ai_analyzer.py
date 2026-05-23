import json
import re

from google import genai
from google.genai import types

from app.config import settings


client = genai.Client(api_key=settings.GEMINI_API_KEY)


def extract_json(text: str) -> dict:
    """
    Иногда ИИ может вернуть JSON с лишним текстом.
    Эта функция пытается достать JSON из ответа.
    """
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("Gemini не вернул JSON")

    return json.loads(match.group(0))


async def analyze_site_structure(
    url: str,
    screenshot_path: str,
    page_text: str
) -> dict:
    with open(screenshot_path, "rb") as file:
        image_bytes = file.read()

    prompt = f"""
Ты — ИИ-аналитик структуры сайтов и специалист по Tilda.

Пользователь дал ссылку на сайт:
{url}

Твоя задача:
- Не копировать сайт.
- Не копировать тексты.
- Не копировать изображения.
- Не генерировать HTML, CSS или JavaScript.
- Только определить структуру страницы.
- Вернуть список пустых блоков Tilda, которые нужно поставить в редакторе.

Бот будет только добавлять пустые блоки.
Он НЕ будет заполнять тексты, картинки, кнопки, цвета и настройки.

Разрешенные типы секций:
hero, features, about, services, gallery, reviews, pricing, faq, form, footer, other.

HTML-текст страницы:
{page_text}

Верни строго JSON без пояснений.

Формат:

{{
  "page_type": "landing",
  "sections": [
    {{
      "order": 1,
      "section_type": "hero",
      "human_name": "Первый экран",
      "reason": "На странице есть крупный первый экран с заголовком и кнопкой"
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png"
                    ),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    if not response.text:
        raise ValueError("Gemini вернул пустой ответ")

    return extract_json(response.text)
