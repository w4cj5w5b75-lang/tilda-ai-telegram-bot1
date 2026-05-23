import re

from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.site_capture import capture_site
from app.ai_analyzer import analyze_site_structure
from app.tilda_builder import TildaBuilder


router = Router()

# Для MVP храним планы прямо в памяти.
# После перезапуска бота они очищаются.
USER_PLANS = {}


def extract_url(text: str) -> str | None:
    pattern = r"(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*)"
    match = re.search(pattern, text or "")

    if not match:
        return None

    url = match.group(1)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет!\n\n"
        "Пришлите ссылку на сайт.\n\n"
        "Я проанализирую структуру страницы, предложу список пустых блоков Tilda "
        "и после подтверждения попробую поставить эти блоки в Tilda.\n\n"
        "Я не копирую тексты, картинки и дизайн. Только создаю каркас из блоков."
    )


@router.message(F.text)
async def handle_url(message: types.Message):
    url = extract_url(message.text)

    if not url:
        await message.answer(
            "Пришлите ссылку на сайт.\n\n"
            "Например:\n"
            "https://example.com"
        )
        return

    chat_id = message.chat.id

    await message.answer("🔎 Принял ссылку. Проверяю сайт.")
    await message.answer("🌐 Открываю сайт в браузере и делаю скриншот.")

    try:
        captured = await capture_site(url)

        await message.answer("🧠 Передаю скриншот ИИ для анализа структуры.")

        analysis = await analyze_site_structure(
            url=url,
            screenshot_path=captured["fullpage_screenshot"],
            page_text=captured["text"],
        )

        sections = analysis.get("sections", [])

        if not sections:
            await message.answer("❌ Не удалось определить секции страницы.")
            return

        USER_PLANS[chat_id] = {
            "url": url,
            "analysis": analysis,
            "sections": sections,
        }

        lines = [
            "✅ Я определил структуру страницы.",
            "",
            "План пустого каркаса Tilda:",
            "",
        ]

        for section in sections:
            order = section.get("order", "?")
            human_name = section.get("human_name", "Блок")
            section_type = section.get("section_type", "other")
            reason = section.get("reason", "")

            lines.append(f"{order}. {human_name} ({section_type})")

            if reason:
                lines.append(f"   Причина: {reason}")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏗 Собрать в Tilda",
                        callback_data="build_tilda"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="cancel_build"
                    )
                ]
            ]
        )

        await message.answer(
            "\n".join(lines),
            reply_markup=keyboard
        )

    except Exception as error:
        await message.answer(
            "❌ Ошибка анализа сайта.\n\n"
            f"Техническая причина:\n{error}"
        )


@router.callback_query(F.data == "cancel_build")
async def cancel_build(callback: CallbackQuery):
    USER_PLANS.pop(callback.message.chat.id, None)

    await callback.message.answer("Ок, сборку отменил.")
    await callback.answer()


@router.callback_query(F.data == "build_tilda")
async def build_tilda(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    plan = USER_PLANS.get(chat_id)

    if not plan:
        await callback.message.answer(
            "❌ План не найден. Пришлите ссылку заново."
        )
        await callback.answer()
        return

    sections = plan["sections"]

    await callback.message.answer(
        "🏗 Начинаю сборку пустых блоков в Tilda."
    )

    builder = TildaBuilder()

    async def progress(text: str):
        await callback.message.answer(text)

    try:
        await builder.build_page(
            sections,
            progress_callback=progress
        )

    except Exception as error:
        await callback.message.answer(
            "❌ Ошибка сборки в Tilda.\n\n"
            "Скорее всего, Tilda изменила текст кнопки или интерфейс отличается.\n"
            "Нужно будет поправить селекторы в файле app/tilda_builder.py.\n\n"
            f"Техническая причина:\n{error}"
        )

    await callback.answer()
