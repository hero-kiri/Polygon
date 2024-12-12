import redis
import httpx
import json
from apscheduler.schedulers.background import BackgroundScheduler
import os
import dotenv
import logging

dotenv.load_dotenv()
logging.basicConfig(level=logging.DEBUG)

HOST = os.getenv("REDIS_HOST")
PORT = os.getenv("REDIS_PORT")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

redis_client = redis.Redis(host=HOST, port=PORT, db=1)

def get_all_keys():
    return redis_client.keys('*')

async def fetch_new_data(ticker, multiplier, timespan, start_date, end_date):
    
    url = f"{BASE_URL}/{ticker}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
    params = {"apiKey": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch data for {ticker}: {response.status_code}")
            return None

async def update_data_in_redis(ticker, multiplier, timespan, start_date, end_date):
    cache_key = f"{ticker}:{multiplier}:{timespan}:{start_date}:{end_date}"
    new_data = await fetch_new_data(ticker, multiplier, timespan, start_date, end_date)
    
    if new_data:
        redis_client.setex(cache_key, 3600, json.dumps(new_data))
        logging.info(f"Updated data for key: {cache_key}")
    else:
        logging.warning(f"Failed to update data for key: {cache_key}")

async def refresh_data():
    keys = get_all_keys()
    for key in keys:
        ticker, multiplier, timespan, start_date, end_date = key.split(':')
        await update_data_in_redis(ticker, multiplier, timespan, start_date, end_date)

def start_scheduler():
    logging.info("Starting scheduler")
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data, 'interval', hours=1)
    scheduler.start()

    import atexit
    atexit.register(lambda: scheduler.shutdown())

