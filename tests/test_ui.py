"""
UI автотесты для сайта Aviasales.
Проверяют функциональность и отображение поиска, календаря, пассажиров и дешевых билетов.
"""

import allure
import pytest
from datetime import datetime, timedelta
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from config import Config
from base_page import BasePage
from conftest import driver  # фикстура из conftest


class MainPage(BasePage):
    """Главная страница сайта Aviasales, все необходимые локаторы и методы."""

    # Локаторы элементов
    ORIGIN_INPUT: tuple = (By.CSS_SELECTOR, "[data-test-id='origin-autocomplete-field']")
    DESTINATION_INPUT: tuple = (By.CSS_SELECTOR, "[data-test-id='destination-autocomplete-field']")
    DEPARTURE_DATE_FIELD: tuple = (By.CSS_SELECTOR, "[data-test-id='departure-date-field']")
    SEARCH_BUTTON: tuple = (By.CSS_SELECTOR, "[data-test-id='form-submit']")
    PASSENGERS_FIELD: tuple = (By.CSS_SELECTOR, "[data-test-id='passengers-field']")
    PASSENGERS_MENU: tuple = (By.CSS_SELECTOR, "[data-test-id='passengers-menu']")
    CHILD_AGE_HINT: tuple = (By.XPATH, "//*[contains(text(),'до 12 лет') or contains(text(),'child')]")
    CHEAP_TICKETS_LINK: tuple = (By.XPATH, "//a[contains(text(),'Самые дешевые')]")
    CHEAP_TICKETS_LIST: tuple = (By.CSS_SELECTOR, "[data-test-id='cheap-tickets-list']")
    TICKET_PRICE: tuple = (By.CSS_SELECTOR, "[data-test-id='price']")
    SUGGESTION_ITEM: tuple = (By.CSS_SELECTOR, "[data-test-id='suggest-item']")
    DATE_CELL: str = "[data-date='{date}']"

    @allure.step("Открыть главную страницу")
    def open(self) -> None:
        """Переход на главную страницу Aviasales."""
        self.driver.get(Config.BASE_URL)
        self.driver.maximize_window()

    @allure.step("Ввод города отправления: {city}")
    def set_origin(self, city: str) -> None:
        """Заполнение поля 'Откуда' и выбор первого варианта."""
        self.send_keys(self.ORIGIN_INPUT, city)
        self.wait.until(EC.presence_of_element_located(self.SUGGESTION_ITEM))
        first_option = (By.CSS_SELECTOR, "[data-test-id='suggest-item']:first-child")
        self.click(first_option)

    @allure.step("Ввод города назначения: {city}")
    def set_destination(self, city: str) -> None:
        """Заполнение поля 'Куда' и выбор первого варианта."""
        self.send_keys(self.DESTINATION_INPUT, city)
        self.wait.until(EC.presence_of_element_located(self.SUGGESTION_ITEM))
        first_option = (By.CSS_SELECTOR, "[data-test-id='suggest-item']:first-child")
        self.click(first_option)

    @allure.step("Выбор даты вылета: {departure_date}")
    def set_departure_date(self, departure_date: str) -> None:
        """Выбор даты в календаре."""
        self.click(self.DEPARTURE_DATE_FIELD)
        date_locator = (By.CSS_SELECTOR, self.DATE_CELL.format(date=departure_date))
        self.click(date_locator)

    @allure.step("Проверка кликабельности кнопки поиска")
    def is_search_button_enabled(self) -> bool:
        """Проверяет, активна ли кнопка 'Найти билеты'."""
        try:
            return self.find_clickable(self.SEARCH_BUTTON).is_enabled()
        except:
            return False

    @allure.step("Открыть меню выбора пассажиров")
    def open_passengers_menu(self) -> None:
        """Клик по полю пассажиров для открытия выпадающего меню."""
        self.click(self.PASSENGERS_FIELD)

    @allure.step("Получить текст подсказки о возрасте ребенка")
    def get_child_age_hint(self) -> str:
        """Возвращает текст подсказки о возрасте ребенка."""
        return self.get_text(self.CHILD_AGE_HINT)

    @allure.step("Перейти к блоку самых дешевых билетов")
    def go_to_cheap_tickets(self) -> None:
        """Клик по ссылке 'Самые дешевые авиабилеты'."""
        self.click(self.CHEAP_TICKETS_LINK)

    @allure.step("Получить список цен на дешевые билеты")
    def get_cheap_tickets_prices(self) -> List[str]:
        """Собирает тексты всех цен из блока дешевых билетов."""
        prices = self.driver.find_elements(*self.TICKET_PRICE)
        return [p.text for p in prices if p.text.strip()]

    @allure.step("Получить список вариантов автоподстановки")
    def get_suggest_items_text(self) -> List[str]:
        """Возвращает текст всех элементов выпадающего списка подсказок."""
        items = self.driver.find_elements(*self.SUGGESTION_ITEM)
        return [item.text for item in items]

    @allure.step("Проверить, что дата недоступна для выбора")
    def is_date_disabled(self, date_str: str) -> bool:
        """Проверяет, заблокирована ли указанная дата в календаре."""
        self.click(self.DEPARTURE_DATE_FIELD)
        date_locator = (By.CSS_SELECTOR, self.DATE_CELL.format(date=date_str))
        element = self.find_element(date_locator)
        disabled = element.get_attribute("aria-disabled") == "true"
        disabled_class = "disabled" in element.get_attribute("class")
        return disabled or disabled_class


@pytest.fixture
def main_page(driver) -> MainPage:
    """Фикстура, возвращающая экземпляр главной страницы."""
    page = MainPage(driver)
    page.open()
    return page


@allure.feature("UI Aviasales")
@allure.severity(allure.severity_level.CRITICAL)
class TestAviasales:
    """Набор UI тестов для сайта Aviasales."""

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
            assert main_page.is_date_disabled(yesterday), \
                f"Прошедшая дата {yesterday} доступна для выбора"

    @allure.title("Кнопка 'Найти билеты' кликабельна только при заполнении обязательных полей")
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
        with allure.step("Проверить наличие текста с возрастом ребенка"):
            hint = main_page.get_child_age_hint()
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
