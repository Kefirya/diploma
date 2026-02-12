"""
API автотесты для Aviasales
"""

import allure
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from requests import Response, Session
from config import Config


# ==================== config.py ====================
"""
Конфигурация API тестов.
"""
class Config:
    """Настройки API тестов."""
    SUGGEST_API_URL: str = "https://autocomplete.travelpayouts.com/places2"
    FLIGHT_API_URL: str = "https://api.travelpayouts.com/v1/flights/search"
    TOKEN: str = "yourapikeyhere"  # замените на реальный токен
    EMAIL: str = "lime91@dollicons.com"
    TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    RETRY_DELAY: int = 1


# ==================== base_api_client.py ====================
"""
Базовый класс для работы с API.
Содержит методы отправки запросов, обработки ответов и повторных попыток.
"""

class BaseApiClient:
    """Базовый API клиент с повторными попытками и обработкой ошибок."""

    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        """
        Инициализация клиента.

        :param base_url: базовый URL API
        :param token: токен авторизации (если требуется)
        """
        self.base_url = base_url
        self.token = token
        self.session = Session()
        if token:
            self.session.headers.update({"Authorization": f"Token {token}"})

    @allure.step("Отправка {method} запроса на {url}")
    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = Config.TIMEOUT,
        retry: int = Config.RETRY_COUNT,
    ) -> Response:
        """
        Универсальный метод отправки запроса с повторными попытками.

        :param method: HTTP метод (GET, POST, etc.)
        :param url: полный URL или путь относительно base_url
        :param params: параметры query string
        :param json: тело запроса в формате JSON
        :param headers: дополнительные заголовки
        :param timeout: таймаут запроса
        :param retry: количество повторных попыток при ошибках
        :return: объект Response
        :raises AssertionError: если все попытки неудачны
        """
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"
        for attempt in range(retry):
            try:
                response = self.session.request(
                    method=method,
                    url=full_url,
                    params=params,
                    json=json,
                    headers=headers,
                    timeout=timeout,
                )
                allure.attach(
                    f"Request: {method} {full_url}\nParams: {params}\nJSON: {json}\nHeaders: {headers}",
                    name="Запрос",
                    attachment_type=allure.attachment_type.TEXT,
                )
                allure.attach(
                    f"Response: {response.status_code}\n{response.text[:1000]}",
                    name="Ответ",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return response
            except Exception as e:
                if attempt == retry - 1:
                    raise AssertionError(f"Запрос не выполнен после {retry} попыток: {e}")
        raise AssertionError("Не удалось выполнить запрос")

    @allure.step("Ожидание успешного ответа с кодом 200")
    def wait_for_ok(self, response: Response) -> Dict[str, Any]:
        """
        Проверка, что статус ответа 200, и возврат JSON.

        :param response: объект Response
        :return: декодированный JSON
        :raises AssertionError: если статус не 200
        """
        assert response.status_code == 200, f"Ожидался код 200, получен {response.status_code}: {response.text}"
        return response.json()


# ==================== suggest_api.py ====================
"""
Клиент для API автодополнения аэропортов и городов.
"""

class SuggestApiClient(BaseApiClient):
    """Клиент для эндпоинта /places2 (автодополнение)."""

    def __init__(self) -> None:
        """Инициализация клиента автодополнения без авторизации."""
        super().__init__(base_url=Config.SUGGEST_API_URL, token=None)

    @allure.step("Поиск мест по запросу '{term}' (метод POST)")
    def search_places_post(
        self,
        term: str,
        locale: str = "ru",
        types: List[str] = ["city", "airport"],
    ) -> Dict[str, Any]:
        """
        Поиск городов/аэропортов через POST-запрос.
        Параметры передаются в query string (API игнорирует метод).

        :param term: поисковый запрос
        :param locale: язык ответа (ru/en)
        :param types: типы объектов (city, airport, etc.)
        :return: JSON ответа
        """
        params = {
            "term": term,
            "locale": locale,
            "types[]": types,
        }
        response = self._request("POST", "", params=params)
        return self.wait_for_ok(response)

    @allure.step("Поиск мест по запросу '{term}' (метод GET)")
    def search_places_get(
        self,
        term: str,
        locale: str = "ru",
        types: List[str] = ["city", "airport"],
    ) -> Dict[str, Any]:
        """
        Поиск городов/аэропортов через GET-запрос.

        :param term: поисковый запрос
        :param locale: язык ответа
        :param types: типы объектов
        :return: JSON ответа
        """
        params = {
            "term": term,
            "locale": locale,
            "types[]": types,
        }
        response = self._request("GET", "", params=params)
        return self.wait_for_ok(response)

    @allure.step("Извлечение названий городов из ответа")
    def extract_city_names(self, response_json: Dict[str, Any]) -> List[str]:
        """
        Извлекает названия городов из ответа API.

        :param response_json: JSON ответа от /places2
        :return: список названий городов (без дублирования)
        """
        cities = set()
        for item in response_json:
            if item.get("type") == "city":
                city_name = item.get("name") or item.get("city_name")
                if city_name:
                    cities.add(city_name)
        return list(cities)

    @allure.step("Извлечение кодов IATA из ответа")
    def extract_iata_codes(self, response_json: Dict[str, Any]) -> List[str]:
        """
        Извлекает IATA коды аэропортов из ответа API.

        :param response_json: JSON ответа от /places2
        :return: список IATA кодов
        """
        codes = []
        for item in response_json:
            if item.get("type") == "airport" and item.get("code"):
                codes.append(item["code"])
        return codes


# ==================== flight_api.py ====================
"""
Клиент для API поиска авиабилетов.
"""

class FlightSearchApiClient(BaseApiClient):
    """Клиент для эндпоинта /v1/flights/search (поиск билетов)."""

    def __init__(self) -> None:
        """Инициализация клиента с токеном авторизации."""
        super().__init__(base_url=Config.FLIGHT_API_URL, token=Config.TOKEN)

    @allure.step("Поиск билетов с параметрами")
    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        trip_class: int = 0,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
    ) -> Dict[str, Any]:
        """
        Поиск авиабилетов через POST-запрос (требуется ввести свой токен).

        :param origin: IATA код города вылета
        :param destination: IATA код города прилёта
        :param depart_date: дата вылета (ГГГГ-ММ-ДД)
        :param return_date: дата возвращения (для туда-обратно)
        :param trip_class: класс перелёта (0 — эконом, 1 — бизнес, 2 — первый)
        :param adults: количество взрослых
        :param children: количество детей
        :param infants: количество младенцев
        :return: JSON ответа от API
        """
        payload = {
            "origin": origin,
            "destination": destination,
            "depart_date": depart_date,
            "return_date": return_date,
            "trip_class": trip_class,
            "adults": adults,
            "children": children,
            "infants": infants,
        }
        # Удаляем None значения
        payload = {k: v for k, v in payload.items() if v is not None}

        response = self._request("POST", "", json=payload)
        return self.wait_for_ok(response)


# ==================== test_api_aviasales.py ====================
"""
API тесты Aviasales.
"""

@allure.feature("API Aviasales")
@allure.severity(allure.severity_level.CRITICAL)
class TestAviasalesAPI:
    """Набор API тестов для Aviasales/Travelpayouts."""

    @pytest.fixture
    def suggest_client(self) -> SuggestApiClient:
        """Фикстура клиента автодополнения."""
        return SuggestApiClient()

    @pytest.fixture
    def flight_client(self) -> FlightSearchApiClient:
        """Фикстура клиента поиска билетов (требует токен)."""
        return FlightSearchApiClient()

    @allure.title("Поиск города на кириллице (POST)")
    @allure.description("Проверка, что поиск по слову 'Сочи' возвращает город Сочи")
    def test_search_city_cyrillic_post(self, suggest_client: SuggestApiClient) -> None:
        """Тест POST-запроса на поиск города по кириллическому названию."""
        with allure.step("Отправить POST запрос с term='Сочи'"):
            response = suggest_client.search_places_post(term="Сочи", locale="ru")
        
        with allure.step("Извлечь названия городов из ответа"):
            cities = suggest_client.extract_city_names(response)
        
        with allure.step("Проверить, что Сочи присутствует в результатах"):
            assert "Сочи" in cities, f"Город Сочи не найден в ответе: {cities}"

    @allure.title("Поиск города по коду аэропорта (POST)")
    @allure.description("Проверка, что поиск по IATA коду 'AER' возвращает аэропорт Адлер (Сочи)")
    def test_search_by_airport_code_post(self, suggest_client: SuggestApiClient) -> None:
        """Тест POST-запроса на поиск аэропорта по IATA коду."""
        with allure.step("Отправить POST запрос с term='AER'"):
            response = suggest_client.search_places_post(term="AER", locale="ru")
        
        with allure.step("Извлечь IATA коды аэропортов"):
            codes = suggest_client.extract_iata_codes(response)
        
        with allure.step("Проверить, что код AER присутствует"):
            assert "AER" in codes, f"Код AER не найден в ответе: {codes}"

    @allure.title("Поиск города GET-методом")
    @allure.description("Проверка, что поиск через GET также работает и возвращает корректные данные")
    def test_search_city_get(self, suggest_client: SuggestApiClient) -> None:
        """Тест GET-запроса на поиск города."""
        with allure.step("Отправить GET запрос с term='Москва'"):
            response = suggest_client.search_places_get(term="Москва", locale="ru")
        
        with allure.step("Извлечь названия городов"):
            cities = suggest_client.extract_city_names(response)
        
        with allure.step("Проверить, что Москва присутствует"):
            assert "Москва" in cities, f"Город Москва не найден: {cities}"

    @allure.title("Поиск билетов с прошедшей датой")
    @allure.description("При указании даты вылета в прошлом API должно вернуть ошибку или пустой результат")
    def test_flight_search_past_date(self, flight_client: FlightSearchApiClient) -> None:
        """Тест поиска билетов с прошедшей датой."""
        past_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        with allure.step(f"Отправить запрос с датой {past_date}"):
            try:
                response = flight_client.search_flights(
                    origin="MOW",
                    destination="AER",
                    depart_date=past_date,
                )
            except AssertionError as e:
                # Если запрос завершился ошибкой (например, 400), это допустимо
                with allure.step("API вернул ошибку — ожидаемое поведение"):
                    assert "400" in str(e) or "ошибка" in str(e).lower(), f"Неожиданная ошибка: {e}"
                return
        
        # Если ответ успешный, проверим, что билетов нет или дата игнорируется
        with allure.step("Проверить, что поиск не вернул предложений"):
            assert "data" in response, "Отсутствует поле data в ответе"
            assert len(response.get("data", [])) == 0, f"Найдены билеты с прошедшей датой: {response['data']}"

    @allure.title("Поиск города на латинице (POST)")
    @allure.description("Проверка, что поиск по латинице 'Sochi' возвращает город Сочи")
    def test_search_city_latin_post(self, suggest_client: SuggestApiClient) -> None:
        """Тест POST-запроса на поиск города по латинице."""
        with allure.step("Отправить POST запрос с term='Sochi'"):
            response = suggest_client.search_places_post(term="Sochi", locale="en")
        
        with allure.step("Извлечь названия городов"):
            cities = suggest_client.extract_city_names(response)
        
        with allure.step("Проверить, что 'Sochi' присутствует в английском названии"):
            # API может вернуть как "Sochi", так и "Сочи" в зависимости от локали
            # Проверим наличие подстроки "Sochi" или "Сочи"
            city_names_lower = [c.lower() for c in cities]
            assert any("sochi" in name or "сочи" in name for name in city_names_lower), \
                f"Город Sochi/Сочи не найден: {cities}"
