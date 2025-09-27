# -*- coding: utf-8 -*-
"""
MyWeather-Seniverse  – 免费版心知天气聚合 API
MIT License · Copyright (c) 2025 heimao <your@email.com>
Data Source: Seniverse Free Tier (https://www.seniverse.com)
"""
import os
import json
import asyncio
import aiohttp
from typing import Literal, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from collections import deque
import time

# -------------------- 配置 --------------------
HOST = "https://api.seniverse.com/v3"
KEYS = [k.strip() for k in (os.getenv("SENIVERSE_KEYS") or "").split(",") if k.strip()]
SINGLE_KEY = os.getenv("SENIVERSE_KEY")
if not (KEYS or SINGLE_KEY):
    raise RuntimeError("请设置 SENIVERSE_KEYS 或 SENIVERSE_KEY")

# -------------------- 多 key 轮询池 --------------------
class KeyPool:
    def __init__(self, keys: list, cool_minutes: float = 10):
        self._q = deque(keys)
        self._cool: dict[str, float] = {}
        self._lock = asyncio.Lock()
        self.cool_sec = cool_minutes * 60

    async def get(self) -> Optional[str]:
        async with self._lock:
            while True:
                if all(time.time() < self._cool.get(k, 0) for k in self._q):
                    return None
                key = self._q.popleft()
                if time.time() >= self._cool.get(key, 0):
                    return key
                self._q.append(key)

    async def report_invalid(self, key: str):
        async with self._lock:
            self._cool[key] = time.time() + self.cool_sec
            if key not in self._q:
                self._q.append(key)

pool = KeyPool(KEYS) if KEYS else None

async def get_key() -> str:
    if pool is None:
        return SINGLE_KEY  # type: ignore
    key = await pool.get()
    if key is None:
        raise HTTPException(503, "All keys cooling")
    return key

# -------------------- 通用请求 --------------------
async def seni_get(endpoint: str, params: dict) -> dict:
    key = await get_key()
    params["key"] = key
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as ses:
            async with ses.get(HOST + endpoint, params=params) as r:
                if r.status in (429, 403):  # 被限速
                    if pool:
                        await pool.report_invalid(key)
                    return await seni_get(endpoint, params)  # 换 key 重试
                r.raise_for_status()
                data = await r.json()
                if data.get("status") != 0:
                    raise HTTPException(400, data.get("status_text", "Seniverse error"))
                return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))

# -------------------- FastAPI --------------------
app = FastAPI(
    title="MyWeather-Seniverse",
    description="聚合心知天气免费接口，支持多 key 轮询、多语言、多单位。",
    version="1.0.0",
    docs_url="/",
)

LANG = Literal["zh-Hans", "zh-Hant", "en", "ja", "de", "fr", "es"]
UNITS = Literal["c", "f"]

# ---------- 单接口 ----------
@app.get("/now")
async def now(location: str = Query(..., example="beijing"),
              lang: LANG = "en", unit: UNITS = "c"):
    return await seni_get("/weather/now.json", {"location": location, "language": lang, "unit": unit})

@app.get("/daily")
async def daily(location: str = Query(..., example="beijing"),
                days: int = Query(3, ge=1, le=3),
                lang: LANG = "en", unit: UNITS = "c"):
    return await seni_get("/weather/daily.json",
                          {"location": location, "days": str(days), "language": lang, "unit": unit})

@app.get("/life")
async def life(location: str = Query(..., example="beijing"),
               lang: LANG = "en"):
    return await seni_get("/life/suggestion.json", {"location": location, "language": lang})

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
