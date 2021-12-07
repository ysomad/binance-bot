import json


SAFE_MODE = True

BROWSER_VERSION = 97

PRODUCT_ID = 163164431084832768
PRODUCT_AMOUNT = 5
SALE_START_TIMESTAMP = 1638874798

ATTEMPTS_NUMBER = 1000
DEFAULT_TIMEOUT = 15

COOKIES_DUMP_PATH = './cookies.pkl'
PURCHASE_PAYLOAD = json.dumps({'number': PRODUCT_AMOUNT, 'productId': PRODUCT_ID})

HOMEPAGE_URL = 'https://binance.com/ru/nft'
PURCHASE_URL = 'https://www.binance.com/bapi/nft/v1/private/nft/mystery-box/purchase'
SALE_URL = f'https://www.binance.com/ru/nft/blindBox/detail?productId={PRODUCT_ID}&number={PRODUCT_AMOUNT}'