import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from main_page import MainPage
from settings import settings


@pytest.fixture(scope="function")
def driver():
    """
    Фикстура, создающая экземпляр веб-драйвера Chrome.
    После завершения теста драйвер автоматически закрывается.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(settings.IMPLICIT_WAIT)
    yield driver
    driver.quit()


@pytest.fixture
def main_page(driver) -> MainPage:
    """Фикстура, возвращающая экземпляр главной страницы (уже открытой)."""
    page = MainPage(driver)
    page.open()
    return page

    driver.implicitly_wait(Config.IMPLICIT_WAIT)
    yield driver
    driver.quit()
