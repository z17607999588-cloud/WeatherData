import asyncio, time, random
from typing import List, Optional
from collections import deque

class KeyPool:
    """
    线程安全、带冷却的多 key 轮询池
    """
    def __init__(self, keys: List[str], cool_minutes: float = 10):
        if not keys:
            raise ValueError("keys 不能为空")
        self._queue = deque(keys)          # 可用 key
        self._cool = {}                    # key -> 解除冷却时间
        self._lock = asyncio.Lock()
        self.cool = cool_minutes * 60

    async def get(self) -> Optional[str]:
        """轮询拿到一个非冷却 key"""
        async with self._lock:
            while True:
                # 全部在冷却
                if all(time.time() < self._cool.get(k, 0) for k in self._queue):
                    return None
                key = self._queue.popleft()
                if time.time() >= self._cool.get(key, 0):
                    return key
                # 仍在冷却，放回尾部
                self._queue.append(key)

    async def report_invalid(self, key: str):
        """接口返回 429/403 等限速/失效时调用"""
        async with self._lock:
            self._cool[key] = time.time() + self.cool
            # 放到尾部，等待冷却结束再重试
            if key not in self._queue:
                self._queue.append(key)

# ---------- 全局池 ----------
keys = [k.strip() for k in (os.getenv("SENIVERSE_KEYS") or "").split(",") if k.strip()]
pool = KeyPool(keys) if keys else None
