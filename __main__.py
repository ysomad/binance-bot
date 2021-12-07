import asyncio
import os
import pickle
import time

from typing import Any

import aiohttp

import cfg
from logger import get_logger

import aiohttp
from seleniumwire import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager


log = get_logger(__name__)


def print_hello() -> None:
    print('\n')
    print('   ▄██   ▄      ▄████████  ▄██████▄    ▄▄▄▄███▄▄▄▄      ▄████████ ████████▄  ')
    print('   ███   ██▄   ███    ███ ███    ███ ▄██▀▀▀███▀▀▀██▄   ███    ███ ███   ▀███ ') 
    print('   ███▄▄▄███   ███    █▀  ███    ███ ███   ███   ███   ███    ███ ███    ███ ')
    print('   ▀▀▀▀▀▀███   ███        ███    ███ ███   ███   ███   ███    ███ ███    ███ ')
    print('   ▄██   ███ ▀███████████ ███    ███ ███   ███   ███ ▀███████████ ███    ███ ')
    print('   ███   ███          ███ ███    ███ ███   ███   ███   ███    ███ ███    ███ ')
    print('   ███   ███    ▄█    ███ ███    ███ ███   ███   ███   ███    ███ ███   ▄███ ')
    print('    ▀█████▀   ▄████████▀   ▀██████▀   ▀█   ███   █▀    ███    █▀  ████████▀  ')
    print('\n')
    print('                       ▀█████████▄   ▄██████▄      ███                       ')
    print('                         ███    ███ ███    ███ ▀█████████▄                   ')
    print('                         ███    ███ ███    ███    ▀███▀▀██                   ')
    print('                        ▄███▄▄▄██▀  ███    ███     ███   ▀                   ')
    print('                       ▀▀███▀▀▀██▄  ███    ███     ███                       ')
    print('                         ███    ██▄ ███    ███     ███                       ')
    print('                         ███    ███ ███    ███     ███                       ')
    print('                       ▄█████████▀   ▀██████▀     ▄████▀                     ')


class CookiesNotFoundErr(Exception):
    pass


class SafeModeErr(Exception):
    pass


def get_chrome_driver() -> webdriver.Chrome:
    s = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=s)


def dump_cookies(driver: webdriver.Chrome) -> None:
    log.info(f'Saving cookies to {cfg.COOKIES_DUMP_PATH}')
    delete_cookies_dump()
    if cfg.SAFE_MODE is False:
        pickle.dump(driver.get_cookies(), open(cfg.COOKIES_DUMP_PATH, 'wb'))


def check_cookies(driver: webdriver.Chrome) -> None:
    """Looking for login button to check if cookies are loaded correctly."""

    log.info('Checking if cookies are loaded correctly')
    try:
        driver.refresh()
        WebDriverWait(driver, 5).until(
            ec.visibility_of_element_located((By.XPATH, '//*[@id="header_login"]'))
        )
        log.info('Cookies are not loaded, manual login needed')
        raise CookiesNotFoundErr
    except TimeoutException:
        log.info('Cookies loaded')


def load_cookies(driver: webdriver.Chrome) -> None:
    """Adds cookies from pickle dump to selenium driver."""

    if cfg.SAFE_MODE:
        log.info('Safe mod detected!')
        raise SafeModeErr

    log.info('Looking for cookies dump')

    try:
        cookies = pickle.load(open(cfg.COOKIES_DUMP_PATH, 'rb'))
    except FileNotFoundError:
        log.info('Cookies dump not found, manual login needed')
        raise CookiesNotFoundErr

    for cookie in cookies:
        driver.add_cookie(cookie)

    check_cookies(driver)
   

def open_home_page(driver: webdriver.Chrome) -> None:
    log.info(f'Redirect to {cfg.HOMEPAGE_URL}')
    driver.get(cfg.HOMEPAGE_URL)


def delete_cookies_dump() -> None:
    if os.path.exists(cfg.COOKIES_DUMP_PATH):
        os.remove(cfg.COOKIES_DUMP_PATH)


def open_login_page(driver: webdriver.Chrome) -> None:
    log.info('Looking for login button')

    login_btn = WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located((By.XPATH, '//*[@id="header_login"]'))
    )
    login_btn.click()

    log.info('Redirect to login page')


def handle_manual_login() -> None:
    log.info('Waiting for manual login')
    _ = input('Press Enter after successful login..')


def open_sale_page(driver: webdriver.Chrome) -> None:
    log.info(f'Redirect to {cfg.SALE_URL}')
    driver.get(cfg.SALE_URL)


def click_buy_and_confirm(driver: webdriver.Chrome, timeout: int) -> None:
    """Waiting for Buy button to appear, clicks it and clicks Confirm"""

    log.info('Looking for Buy button')
    buy_btn = WebDriverWait(driver, timeout).until(
        ec.visibility_of_element_located(
            (By.XPATH, '//button[contains(text(),"Купить")]')
        )
    )
    buy_btn.click()
    log.info('Buy button clicked')

    log.info('Looking for Confirm button')
    confirm_btn = WebDriverWait(driver, timeout).until(
        ec.visibility_of_element_located(
            (By.XPATH, '//button[contains(text(),"Подтвердить")]')
        )
    )
    confirm_btn.click()
    log.info('Confirm button clicked')


def get_request_headers(driver: webdriver.Chrome) -> dict[str, Any]:
    log.info('Waiting for request to get headers')

    request = driver.wait_for_request('/bapi/nft/v1/private/nft/nft-trade/order-create')

    log.info('Got request, generating headers')

    cookies = request.headers['cookie']
    csrftoken = request.headers['csrftoken']
    deviceinfo='eyJzY3JlZW5fcmVzb2x1dGlvbiI6Ijg1OCwxNTI1IiwiYXZhaWxhYmxlX3NjcmVlbl9yZXNvbHV0aW9uIjoiODEzLDE1MjUiLCJzeXN0ZW1fdmVyc2lvbiI6IldpbmRvd3MgNyIsImJyYW5kX21vZGVsIjoidW5rbm93biIsInN5c3RlbV9sYW5nIjoiZW4tVVMiLCJ0aW1lem9uZSI6IkdNVCs2IiwidGltZXpvbmVPZmZzZXQiOi0zNjAsInVzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCA2LjE7IFdpbjY0OyB4NjQ7IHJ2OjkzLjApIEdlY2tvLzIwMTAwMTAxIEZpcmVmb3gvOTMuMCIsImxpc3RfcGx1Z2luIjoiIiwiY2FudmFzX2NvZGUiOiIyOWI5YmU4MyIsIndlYmdsX3ZlbmRvciI6Ikdvb2dsZSBJbmMuIiwid2ViZ2xfcmVuZGVyZXIiOiJBTkdMRSAoSW50ZWwoUikgSEQgR3JhcGhpY3MgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wKSIsImF1ZGlvIjoiMzUuNzM4MzI5NTkzMDkyMiIsInBsYXRmb3JtIjoiV2luMzIiLCJ3ZWJfdGltZXpvbmUiOiJBc2lhL0FsbWF0eSIsImRldmljZV9uYW1lIjoiRmlyZWZveCBWOTMuMCAoV2luZG93cykiLCJmaW5nZXJwcmludCI6Ijg3YmY0OTA2ZDU3NDc4ZTE0NjAwMzQwYmY3MWUyYTUzIiwiZGV2aWNlX2lkIjoiIiwicmVsYXRlZF9kZXZpY2VfaWRzIjoiMTYyOTEzODQ2NTA4NHBCVTJIS2JOeWhjRWRKRkpHMGksMTYyOTk4Mjk5NzgwMnBPQWVDMGRmcldqUUZxV2NZTmEsMTYyOTk4NTIzMTY3MXlndGlyOFhBOWZWWW93TWFRRDcifQ=='
    useragent='Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'

    x_nft_checkbot_sitekey = request.headers['x-nft-checkbot-sitekey']
    x_nft_checkbot_token = request.headers['x-nft-checkbot-token']
    x_trace_id = request.headers['x-trace-id']
    x_ui_request_trace  = request.headers['x-ui-request-trace']

    headers = {
        'Host': 'www.binance.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'clienttype': 'web',
        'x-nft-checkbot-token': x_nft_checkbot_token,
        'x-nft-checkbot-sitekey': x_nft_checkbot_sitekey,
        'x-trace-id': x_trace_id,
        'x-ui-request-trace' : x_ui_request_trace,
        'content-type':'application/json',
        'cookie' : cookies,
        'csrftoken': csrftoken,
        'device-info': deviceinfo,
        'user-agent': useragent
    }

    log.info(f'Generated headers: {request.headers}')

    return headers


def get_tasks(session: aiohttp.ClientSession) -> list[asyncio.Task]:
    log.info('Start creating tasks')

    tasks: list[asyncio.Task] = list()

    for _ in range(0, cfg.ATTEMPTS_NUMBER):
        context = session.post(
            cfg.PURCHASE_URL, 
            data=cfg.PURCHASE_PAYLOAD, 
            ssl=False
        )
        task = asyncio.create_task(context)
        tasks.append(task)

    log.info(f'Created {len(tasks)} amount of tasks')

    return tasks


def login(driver: webdriver.Chrome) -> None:
    try:
        load_cookies(driver)
    except CookiesNotFoundErr:
        handle_manual_login()
        dump_cookies(driver)
    except SafeModeErr:
        handle_manual_login()


async def gather_tasks(headers: dict[str, Any]) -> dict:
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = get_tasks(session)
        log.info('Gathering all created tasks')
        await asyncio.gather(*tasks)


def start_buying_attempt(headers: dict[str, Any]) -> None:
    log.info('Starting event loop')
    asyncio.get_event_loop().run_until_complete(gather_tasks(headers))


def wait_for_sale_start():
    log.info('Waiting for sale to start')

    while True:
        now = time.time()
        if cfg.SALE_START_TIMESTAMP > now:
            log.info(f'Seconds left: {cfg.SALE_START_TIMESTAMP - now}')
        else:
            log.info('Sale is starting!')
            break


def main() -> None:
    print_hello()

    driver = get_chrome_driver()
    driver.maximize_window()

    open_sale_page(driver)
    login(driver)

    wait_for_sale_start()
    click_buy_and_confirm(driver, cfg.DEFAULT_TIMEOUT)
    headers = get_request_headers(driver)
    start_buying_attempt(headers)

    log.warning(headers)

    if cfg.SAFE_MODE:
        delete_cookies_dump()
           

if __name__ == '__main__':
    main()