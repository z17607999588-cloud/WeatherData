"""
MyWeather-Seniverse
Free-tier wrapper of Seniverse Weather API (v3)
Author:heimao <your@email.com>
License: MIT
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiohttp, asyncio, json, os
from typing import Literal

app = FastAPI(
    title="MyWeather-Seniverse",
    description="Unofficial wrapper for Seniverse free-tier weather endpoints.",
    version="1.0.0",
    docs_url="/",
)

# ---------- 配置 ----------
KEY = os.getenv("SENIVERSE_KEY")          # 飞线部署时注入
if not KEY:
    raise RuntimeError("SENIVERSE_KEY not found")

HOST = "https://api.seniverse.com/v3"
LANG = Literal["zh-Hans", "en", "ja"]
UNITS = Literal["c", "f"]

# ---------- 错误模型 ----------
class Err(BaseModel):
    ok: bool = False
    code: str
    message: str

# ---------- 安全请求 ----------
async def get_seni(endpoint: str, params: dict):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as ses:
            async with ses.get(HOST + endpoint, params=params) as r:
                r.raise_for_status()
                data = await r.json()
                if data.get("status") != 0:
                    raise HTTPException(400, data.get("status_text", "Seniverse error"))
                return data
    except Exception as e:
        raise HTTPException(502, str(e))

# ---------- 三条免费接口 ----------
@app.get("/now")
async def now(location: str = Query(..., example="beijing"),
              lang: LANG = "en", unit: UNITS = "c"):
    return await get_seni("/weather/now.json",
                          {"key": KEY, "location": location, "language": lang, "unit": unit})

@app.get("/daily")
async def daily(location: str = Query(..., example="beijing"),
                days: int = Query(3, ge=1, le=3),
                lang: LANG = "en", unit: UNITS = "c"):
    return await get_seni("/weather/daily.json",
                          {"key": KEY, "location": location, "days": days, "language": lang, "unit": unit})

@app.get("/life")
async def life(location: str = Query(..., example="beijing"),
               lang: LANG = "en"):
    return await get_seni("/life/suggestion.json",
                          {"key": KEY, "location": location, "language": lang})

# ---------- 合并 ----------
@app.get("/all")
async def all_in_one(location: str = Query(..., example="beijing"),
                     days: int = Query(3, ge=1, le=3),
                     lang: LANG = "en", unit: UNITS = "c"):
    tasks = [now(location, lang, unit),
             daily(location, days, lang, unit),
             life(location, lang)]
    res_now, res_daily, res_life = await asyncio.gather(*tasks)
    return {"now": res_now, "daily": res_daily, "life": res_life}
