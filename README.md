# MyWeather-Seniverse

[![Deploy](https://github.com/你的GitHub名/myweather-seniverse/workflows/Deploy%20to%20Fly.io/badge.svg)](https://github.com/你的GitHub名/myweather-seniverse)

基于 Seniverse 免费套餐的轻量级天气聚合 API，支持多语言、多单位、并发查询。

## 快速开始
```bash
git clone https://github.com/你的GitHub名/myweather-seniverse.git
cd myweather-seniverse
cp .env.example .env        # 填写 SENIVERSE_KEY
docker-compose up           # 本地 http://localhost:8080

Weather data is provided by Seniverse (https://www.seniverse.com) under its free-tier terms.
This wrapper does not alter the original data semantics and retains all disclaimers
published by Seniverse. For accuracy or redistribution restrictions please refer to
https://www.seniverse.com/terms
