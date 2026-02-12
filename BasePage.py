"""
Базовый класс Page Object для всех страниц.
Содержит универсальные методы работы с элементами и явные ожидания.
"""

from typing import Tuple, Callable, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import allure
from config import Config


class BasePage:
    """
    Базовый класс, от которого наследуются все Page Object.
    Предоставляет методы для поиска, кликов, ввода текста и проверок.
    """

    def __init__(self, driver: WebDriver) -> None:
        """
        Инициализация базовой страницы.
        
        :param driver: экземпляр веб-драйвера
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, Config.EXPLICIT_WAIT)

    @allure.step("Ожидание появления элемента {locator}")
    def find_element(self, locator: Tuple[By, str]) -> WebElement:
        """
        
        :param locator: локатор элемента (By, value)
        :return: WebElement
        """
        return self.wait.until(EC.presence_of_element_located(locator))

    @allure.step("Ожидание кликабельности элемента {locator}")
    def find_clickable(self, locator: Tuple[By, str]) -> WebElement:
        """
        Явное ожидание кликабельности элемента.
        
        :param locator: локатор элемента
        :return: WebElement
        """
        return self.wait.until(EC.element_to_be_clickable(locator))

    @allure.step("Клик по элементу {locator}")
    def click(self, locator: Tuple[By, str]) -> None:
        """
        Клик по элементу с предварительным ожиданием кликабельности.
        
        :param locator: локатор элемента
        """
        self.find_clickable(locator).click()

    @allure.step("Ввод текста '{text}' в элемент {locator}")
    def send_keys(self, locator: Tuple[By, str], text: str) -> None:
        """
        Очистка поля и ввод текста.
        
        :param locator: локатор поля ввода
        :param text: текст для ввода
        """
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)

    @allure.step("Получение текста элемента {locator}")
    def get_text(self, locator: Tuple[By, str]) -> str:
        """
        Получение видимого текста элемента.
        
        :param locator: локатор элемента
        :return: текст элемента
        """
        return self.find_element(locator).text

    @allure.step("Проверка наличия элемента {locator}")
    def is_element_present(self, locator: Tuple[By, str], timeout: int = 5) -> bool:
        """       
        :param locator: локатор элемента
        :param timeout: время ожидания в секундах
        :return: True если элемент присутствует, иначе False
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Ожидание выполнения пользовательского условия")
    def wait_for_result(self, condition: Callable[[], Any], timeout: int = 10) -> Any:
        """
        
        :param condition: функция-условие, возвращающая не ложное значение
        :param timeout: максимальное время ожидания в секундах
        :return: результат выполнения condition (первое не ложное значение)
        """
        return WebDriverWait(self.driver, timeout).until(lambda _: condition())
