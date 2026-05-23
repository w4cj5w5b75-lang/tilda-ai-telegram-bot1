from playwright.async_api import async_playwright

from config import settings
from tilda_blocks import TILDA_BLOCKS


class TildaBuilder:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=settings.HEADLESS,
            args=["--no-sandbox"]
        )

        self.page = await self.browser.new_page(
            viewport={"width": 1440, "height": 1200}
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

    async def login(self):
        if not settings.TILDA_LOGIN or not settings.TILDA_PASSWORD:
            raise ValueError("Не заданы TILDA_LOGIN или TILDA_PASSWORD")

        page = self.page

        await page.goto(
            "https://tilda.cc/login/",
            wait_until="networkidle",
            timeout=60000
        )

        await page.wait_for_timeout(2000)

        # Поля логина и пароля могут отличаться.
        # Если вход не сработает, нужно будет проверить селекторы.
        await page.fill('input[name="email"]', settings.TILDA_LOGIN)
        await page.fill('input[name="password"]', settings.TILDA_PASSWORD)

        # Пробуем нажать кнопку входа
        possible_login_buttons = [
            "Log in",
            "Login",
            "Sign in",
            "Войти"
        ]

        clicked = False

        for text in possible_login_buttons:
            try:
                await page.get_by_text(text).first.click(timeout=3000)
                clicked = True
                break
            except Exception:
                pass

        if not clicked:
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(7000)

    async def open_project(self):
        if not settings.TILDA_PROJECT_URL:
            raise ValueError("Не указана переменная TILDA_PROJECT_URL")

        await self.page.goto(
            settings.TILDA_PROJECT_URL,
            wait_until="networkidle",
            timeout=60000
        )

        await self.page.wait_for_timeout(3000)

    async def create_new_page(self):
        page = self.page

        possible_buttons = [
            "Create new page",
            "Create page",
            "New page",
            "Создать новую страницу",
            "Создать страницу",
            "Новая страница"
        ]

        clicked = False

        for text in possible_buttons:
            try:
                await page.get_by_text(text).first.click(timeout=5000)
                clicked = True
                break
            except Exception:
                pass

        if not clicked:
            raise ValueError(
                "Не нашел кнопку создания страницы в Tilda. "
                "Нужно поправить селектор в create_new_page()."
            )

        await page.wait_for_timeout(5000)

        # Иногда Tilda предлагает выбрать шаблон.
        # Пробуем выбрать пустую страницу.
        possible_blank_buttons = [
            "Blank page",
            "Empty page",
            "Start from scratch",
            "Пустая страница",
            "Начать с нуля"
        ]

        for text in possible_blank_buttons:
            try:
                await page.get_by_text(text).first.click(timeout=3000)
                await page.wait_for_timeout(3000)
                break
            except Exception:
                pass

    async def open_blocks_library(self):
        page = self.page

        # Прокручиваем вниз редактора
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(1000)

        possible_buttons = [
            "More blocks",
            "All blocks",
            "Add block",
            "Еще блоки",
            "Все блоки",
            "Добавить блок"
        ]

        clicked = False

        for text in possible_buttons:
            try:
                await page.get_by_text(text).first.click(timeout=5000)
                clicked = True
                break
            except Exception:
                pass

        if not clicked:
            raise ValueError(
                "Не нашел кнопку открытия библиотеки блоков. "
                "Нужно поправить селектор в open_blocks_library()."
            )

        await page.wait_for_timeout(3000)

    async def search_block(self, section_type: str):
        page = self.page

        block_info = TILDA_BLOCKS.get(section_type, TILDA_BLOCKS["other"])
        search_words = block_info["search_words"]

        # Ищем поле поиска блоков
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="Search"]',
            'input[placeholder*="Поиск"]',
            'input'
        ]

        for selector in search_selectors:
            try:
                search_input = page.locator(selector).first
                await search_input.fill(search_words[0], timeout=3000)
                await page.wait_for_timeout(2000)
                return
            except Exception:
                pass

        # Если поиска нет, ничего страшного.
        # Тогда ниже попробуем нажать первый подходящий блок.
        return

    async def click_first_available_block(self):
        page = self.page

        possible_add_buttons = [
            "Add",
            "Choose",
            "Select",
            "Добавить",
            "Выбрать"
        ]

        for text in possible_add_buttons:
            try:
                await page.get_by_text(text).first.click(timeout=4000)
                await page.wait_for_timeout(3000)
                return
            except Exception:
                pass

        # Резервный вариант — попробовать кликнуть первую видимую карточку
        possible_card_selectors = [
            ".block",
            ".tpl-card",
            ".js-store-prod",
            "[data-block-id]",
            "div"
        ]

        for selector in possible_card_selectors:
            try:
                await page.locator(selector).first.click(timeout=4000)
                await page.wait_for_timeout(3000)
                return
            except Exception:
                pass

        raise ValueError(
            "Не удалось нажать на блок. "
            "Нужно уточнить селектор карточки блока в Tilda."
        )

    async def add_empty_block(self, section_type: str):
        await self.open_blocks_library()
        await self.search_block(section_type)
        await self.click_first_available_block()

    async def build_page(self, sections: list, progress_callback=None):
        await self.start()

        try:
            if progress_callback:
                await progress_callback("🔐 Захожу в Tilda.")

            await self.login()

            if progress_callback:
                await progress_callback("📁 Открываю проект Tilda.")

            await self.open_project()

            if progress_callback:
                await progress_callback("📄 Создаю новую страницу.")

            await self.create_new_page()

            total = len(sections)

            for index, section in enumerate(sections, start=1):
                section_type = section.get("section_type", "other")
                human_name = section.get("human_name", section_type)

                if progress_callback:
                    await progress_callback(
                        f"➕ Добавляю блок {index}/{total}: {human_name}."
                    )

                await self.add_empty_block(section_type)

            if progress_callback:
                await progress_callback("✅ Пустой каркас страницы собран.")

        finally:
            await self.stop()
