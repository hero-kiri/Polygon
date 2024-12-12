import os
import json
import httpx
import dotenv
import logging

from fastapi import FastAPI, HTTPException
from redis.asyncio import Redis

from .schemas import StockDataRequest
from .services import start_scheduler

dotenv.load_dotenv()
logging.basicConfig(level=logging.DEBUG)
start_scheduler() # Refresh data 

app = FastAPI()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
HOST = os.getenv("REDIS_HOST")
PORT = os.getenv("REDIS_PORT")

redis = Redis(host=HOST, port=PORT)


@app.post("/purchase/")
async def create_purchase(data: StockDataRequest):
    logging.debug(f"Received request: {data}")

    cache_key = f"{data.ticker}:{data.multiplier}:{data.timespan}:{data.start_date}:{data.end_date}"    
    cached_response = await redis.get(cache_key)
    if cached_response:
        logging.debug("Returning cached data")
        data_dict = json.loads(cached_response)
        return {"source": "cache", "data": data_dict}

    try:
        url = f"{BASE_URL}/{data.ticker}/range/{data.multiplier}/{data.timespan}/{data.start_date}/{data.end_date}"
        params = {"apiKey": API_KEY}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            logging.debug(f"Polygon API response: {response.status_code} - {response.text}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())

            stock_data = response.json()
            # Данные хранятся 1 день
            await redis.setex(cache_key, 3600, json.dumps(stock_data))
            return {"source": "polygon", "data": stock_data}
            
    except httpx.RequestError as exc:
        logging.error(f"Error while requesting {exc.request.url!r}: {exc}")
        raise HTTPException(status_code=500, detail="Error while requesting external API")
    except Exception as exc:
        logging.error(f"Unexpected error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
