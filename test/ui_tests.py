import allure
import pytest
from datetime import datetime, timedelta
from selenium.webdriver.support import expected_conditions as EC
from main_page import MainPage


@allure.feature("UI Aviasales")
@allure.story("Поиск авиабилетов")
@allure.severity(allure.severity_level.CRITICAL)
class TestAviasalesUI:
    """Набор UI-тестов для проверки функциональности главной страницы Aviasales."""

    @allure.title("Автоподстановка аэропортов Москвы")
    @allure.description("При вводе 'Москва' в поле 'Откуда' появляются варианты аэропортов Москвы")
    def test_moscow_airport_suggestions(self, main_page: MainPage) -> None:
        """Проверка, что выпадающий список содержит аэропорты Москвы."""
        with allure.step("Ввести 'Москва' в поле отправления"):
            main_page.send_keys(main_page.ORIGIN_INPUT, "Москва")

        with allure.step("Дождаться появления подсказок"):
            main_page.wait.until(EC.presence_of_element_located(main_page.SUGGESTION_ITEM))

        suggestions = main_page.get_suggest_items_text()

        with allure.step("Проверить наличие аэропортов Москвы в подсказках"):
            assert any(
                "Москва" in s or "SVO" in s or "VKO" in s or "DME" in s or "ZIA" in s
                for s in suggestions
            ), f"Не найдены аэропорты Москвы: {suggestions}"

    @allure.title("Календарь: блокировка прошедших дат")
    @allure.description("Прошедшие даты в календаре должны быть неактивны (disabled)")
    def test_past_dates_disabled(self, main_page: MainPage) -> None:
        """Проверка, что вчерашняя дата недоступна для выбора."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        with allure.step(f"Проверить, что дата {yesterday} недоступна"):
            assert main_page.is_date_disabled(yesterday), f"Прошедшая дата {yesterday} доступна для выбора"

    @allure.title("Кнопка 'Найти билеты' активируется после заполнения обязательных полей")
    @allure.description("Кнопка поиска должна быть неактивна, пока не заполнены Откуда, Куда и Дата")
    def test_search_button_enabled_after_filling(self, main_page: MainPage) -> None:
        """Проверка активации кнопки поиска после заполнения полей."""
        with allure.step("Проверить, что изначально кнопка неактивна"):
            assert not main_page.is_search_button_enabled(), "Кнопка активна без заполнения полей"

        with allure.step("Заполнить город отправления"):
            main_page.set_origin("Москва")

        with allure.step("Заполнить город назначения"):
            main_page.set_destination("Санкт-Петербург")

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with allure.step("Выбрать дату вылета (завтра)"):
            main_page.set_departure_date(tomorrow)

        with allure.step("Проверить, что кнопка стала активна"):
            assert main_page.is_search_button_enabled(), "Кнопка не активна после заполнения полей"

    @allure.title("Выпадающее меню пассажиров содержит подсказку о возрасте ребенка")
    @allure.description("В меню выбора пассажиров присутствует текст с возрастным ограничением для ребенка")
    def test_passenger_menu_has_child_age_hint(self, main_page: MainPage) -> None:
        """Проверка наличия подсказки о возрасте ребенка."""
        with allure.step("Открыть меню пассажиров"):
            main_page.open_passengers_menu()

        hint = main_page.get_child_age_hint()
        with allure.step("Проверить наличие текста с возрастом ребенка"):
            assert "до 12" in hint or "child" in hint.lower() or "ребен" in hint, \
                f"Подсказка о возрасте ребенка не найдена: '{hint}'"

    @allure.title("Кнопка 'Самые дешевые авиабилеты' отображает список и цену")
    @allure.description("После клика на ссылку дешевых билетов отображается список направлений с ценами")
    def test_cheap_tickets_display_list_and_price(self, main_page: MainPage) -> None:
        """Проверка, что блок дешевых билетов содержит цены."""
        with allure.step("Перейти к разделу самых дешевых билетов"):
            main_page.go_to_cheap_tickets()

        with allure.step("Дождаться загрузки списка билетов"):
            main_page.wait.until(EC.presence_of_element_located(main_page.CHEAP_TICKETS_LIST))

        prices = main_page.get_cheap_tickets_prices()
        with allure.step("Проверить, что цены отображаются"):
            assert len(prices) > 0, "Список цен пуст"
            assert all("₽" in p or "$" in p or "€" in p for p in prices), \
                f"Не все элементы содержат цену: {prices}"
