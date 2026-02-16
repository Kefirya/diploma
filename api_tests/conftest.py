import pytest
from api_tests.clients.suggest_client import SuggestApiClient
from api_tests.clients.flight_client import FlightSearchApiClient


@pytest.fixture
def suggest_client() -> SuggestApiClient:
    """Фикстура клиента автодополнения."""
    return SuggestApiClient()


@pytest.fixture
def flight_client() -> FlightSearchApiClient:
    """Фикстура клиента поиска билетов (требуется токен)."""
    return FlightSearchApiClient()
