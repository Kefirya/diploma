import allure
import pytest
from datetime import datetime, timedelta
from api_tests.clients.suggest_client import SuggestApiClient
from api_tests.clients.flight_client import FlightSearchApiClient


@allure.feature("API Aviasales")
@allure.story("Поиск городов и аэропортов")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.critical
class TestAviasalesAPI:
    """Набор API-тестов для проверки эндпоинтов Aviasales/Travelpayouts."""

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
    @allure.description("Проверка, что поиск по IATA-коду 'AER' возвращает аэропорт Адлер (Сочи)")
    def test_search_by_airport_code_post(self, suggest_client: SuggestApiClient) -> None:
        """Тест POST-запроса на поиск аэропорта по IATA-коду."""
        with allure.step("Отправить POST запрос с term='AER'"):
            response = suggest_client.search_places_post(term="AER", locale="ru")

        with allure.step("Извлечь IATA-коды аэропортов"):
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
                # Если ответ успешный, проверяем, что данных нет
                with allure.step("Проверить, что поиск не вернул предложений"):
                    assert "data" in response, "Отсутствует поле data в ответе"
                    assert len(response.get("data", [])) == 0, f"Найдены билеты с прошедшей датой: {response['data']}"
            except AssertionError as e:
                # Если запрос завершился ошибкой (например, 400), это допустимо
                with allure.step("API вернул ошибку — ожидаемое поведение"):
                    assert "400" in str(e) or "ошибка" in str(e).lower(), f"Неожиданная ошибка: {e}"

    @allure.title("Поиск города на латинице (POST)")
    @allure.description("Проверка, что поиск по латинице 'Sochi' возвращает город Сочи")
    def test_search_city_latin_post(self, suggest_client: SuggestApiClient) -> None:
        """Тест POST-запроса на поиск города по латинице."""
        with allure.step("Отправить POST запрос с term='Sochi'"):
            response = suggest_client.search_places_post(term="Sochi", locale="en")

        with allure.step("Извлечь названия городов"):
            cities = suggest_client.extract_city_names(response)

        with allure.step("Проверить, что 'Sochi' присутствует в английском названии"):
            city_names_lower = [c.lower() for c in cities]
            assert any("sochi" in name or "сочи" in name for name in city_names_lower), \
                f"Город Sochi/Сочи не найден: {cities}"
