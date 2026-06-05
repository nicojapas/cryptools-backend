# Cryptools Backend

![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?logo=nodedotjs&logoColor=white)
![AWS CDK](https://img.shields.io/badge/AWS_CDK-2.x-FF9900?logo=amazonaws&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-Serverless-FF9900?logo=awslambda&logoColor=white)

Serverless cryptocurrency data API powering a crypto dashboard. Built with AWS CDK and TypeScript.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend  │────▶│ API Gateway  │────▶│ Lambda Functions│
└─────────────┘     │  + API Key   │     └────────┬────────┘
                    │  + CORS      │              │
                    └──────────────┘              ▼
                                          ┌─────────────┐
                                          │  S3 Cache   │
                                          └──────┬──────┘
                                                 ▼
                                          ┌─────────────┐
                                          │ CoinGecko   │
                                          │ CryptoCompare│
                                          └─────────────┘
```

## Endpoints

| Endpoint | Description | Cache |
|----------|-------------|-------|
| `GET /health` | Health check | - |
| `GET /tokens` | Market data: top coins, gainers/losers, trending, sentiment | 5 min |
| `GET /news` | Aggregated crypto news | 1 hour |

## Stack

- **Runtime**: Node.js 22, TypeScript, esbuild
- **Infra**: AWS CDK, Lambda, API Gateway, S3
- **Testing**: Jest

## Setup

```bash
npm install

# Create .env with COINGECKO_API_KEY and CRYPTOCOMPARE_API_KEY

cdk bootstrap  # first time only
cdk deploy
```

## Development

```bash
npm test           # run tests
npx tsc --noEmit   # type check
cdk diff           # preview changes
```

## Structure

```
├── bin/app.ts                 # CDK entry
├── lib/api-stack.ts           # Infrastructure
├── src/
│   ├── handlers/              # Lambda handlers
│   ├── services/              # API integrations (CoinGecko, CryptoCompare)
│   ├── common/                # Cache, config, response utils
│   └── types/                 # TypeScript definitions
└── test/                      # Jest tests
```
