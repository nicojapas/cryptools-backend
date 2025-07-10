# CryptoPanic News API Setup Guide

## Overview
The news endpoint has been updated to fetch real cryptocurrency news from CryptoPanic API with 1-hour caching.

## Security Setup

### Option 1: Environment Variable (Development)
Set the API token as an environment variable before deploying:

```bash
# Windows PowerShell
$env:CRYPTOPANIC_API_TOKEN="your_api_token_here"
cdk deploy

# Windows Command Prompt
set CRYPTOPANIC_API_TOKEN=your_api_token_here
cdk deploy

# Linux/Mac
export CRYPTOPANIC_API_TOKEN="your_api_token_here"
cdk deploy
```

### Option 2: AWS Systems Manager Parameter Store (Production - Recommended)
For production environments, store the API token securely in AWS Systems Manager:

1. **Store the parameter:**
```bash
aws ssm put-parameter \
    --name "/cryptools/cryptopanic-api-token" \
    --value "your_api_token_here" \
    --type "SecureString" \
    --description "CryptoPanic API token for news endpoint"
``` 

2. **Update the CDK stack** to read from Parameter Store (future enhancement)

### Option 3: AWS Secrets Manager (Enterprise)
For enterprise environments with additional security requirements.

## API Token
Get your CryptoPanic API token from: https://cryptopanic.com/developers/api/

## Features
- ✅ **Real-time news** from CryptoPanic
- ✅ **1-hour caching** for performance
- ✅ **Secure token handling** via environment variables
- ✅ **Error handling** and logging
- ✅ **CORS support** for frontend integration

## Response Format
The news endpoint returns:
```json
{
  "data": [
    {
      "id": 12345,
      "title": "Bitcoin reaches new all-time high",
      "summary": "Bitcoin has reached a new all-time high...",
      "source": "CoinDesk",
      "published_at": "2024-01-15T10:00:00Z",
      "url": "https://example.com/news/article",
      "currencies": ["BTC", "ETH"],
      "votes": {"positive": 10, "negative": 2},
      "domain": "coindesk.com"
    }
  ],
  "message": "Cryptocurrency news retrieved successfully",
  "count": 20
}
```

## Deployment
After setting up the API token, deploy your stack:
```bash
cdk deploy
```

## Testing
Test the endpoint:
```bash
curl https://your-api-gateway-url/news
``` 