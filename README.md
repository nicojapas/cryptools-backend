# Cryptools Backend

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![AWS CDK](https://img.shields.io/badge/AWS_CDK-2.175.0-FF9900?logo=amazonaws&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-Serverless-FF9900?logo=awslambda&logoColor=white)
![API Gateway](https://img.shields.io/badge/API_Gateway-REST-FF4F8B?logo=amazonapigateway&logoColor=white)

A serverless cryptocurrency data aggregation API built with AWS CDK. Provides endpoints for market data, news, and blockchain monitoring.

## Features

- **Market Data** - Top coins, gainers, losers, trending tokens via CoinGecko API
- **News Feed** - Trending crypto news from CryptoPanic
- **BSC Token Monitor** - Detects newly deployed ERC20 tokens on Binance Smart Chain
- **S3 Caching** - Reduces external API calls with configurable TTL
- **Market Sentiment** - Calculates sentiment based on BTC price movement

## API Endpoints

| Endpoint | Description | Cache TTL |
|----------|-------------|-----------|
| `GET /tokens` | Market data, top coins, gainers/losers | 60s |
| `GET /news` | Trending crypto news | 1 hour |
| `GET /fetch_bsc_tokens` | Recently deployed BSC tokens | 24 hours |

## Architecture

```
API Gateway → Lambda Functions → External APIs (CoinGecko, CryptoPanic, BSC RPC)
                    ↓
              S3 Cache Bucket
```

## Prerequisites

- Python 3.12+
- [Docker](https://www.docker.com/products/docker-desktop/) (required for Lambda layer bundling)
- AWS CLI configured with appropriate credentials
- Node.js (for AWS CDK CLI)

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate.bat  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export CRYPTOPANIC_API_TOKEN=your_token_here
   ```

## Deployment

Make sure Docker is running, then:

```bash
cdk deploy
```

## Project Structure

```
cryptools-backend/
├── app.py                          # CDK app entry point
├── cryptools_backend_stack.py      # Infrastructure definition
├── cryptools_backend/
│   ├── lambdas/
│   │   ├── config.py               # API configuration
│   │   ├── utils.py                # Response formatting
│   │   ├── s3_utils.py             # S3 caching service
│   │   ├── tokens/                 # /tokens endpoint
│   │   ├── news/                   # /news endpoint
│   │   ├── fetch_bsc_tokens/       # /fetch_bsc_tokens endpoint
│   │   └── services/               # External API integrations
│   └── layers/                     # Lambda layers
└── scripts/
    └── lint.py                     # Code formatting
```

## Useful Commands

| Command | Description |
|---------|-------------|
| `cdk synth` | Synthesize CloudFormation template |
| `cdk deploy` | Deploy stack to AWS |
| `cdk diff` | Compare deployed stack with current state |
| `python scripts/lint.py` | Format code with black, isort, ruff |
