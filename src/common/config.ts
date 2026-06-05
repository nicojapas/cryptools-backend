export const Config = {
  // AWS
  region: process.env.AWS_REGION || 'eu-west-1',
  s3Bucket: process.env.S3_BUCKET!,

  // CryptoCompare API
  cryptocompare: {
    news: 'https://min-api.cryptocompare.com/data/v2/news/',
  },

  // CoinGecko API
  coingecko: {
    topCoins: 'https://api.coingecko.com/api/v3/coins/markets',
    trending: 'https://api.coingecko.com/api/v3/search/trending',
  },

  // Cache durations (seconds)
  cache: {
    default: 60,
    news: 3600,
    tokens: 300, // 5 minutes for token data
  },

  // Request settings
  requestTimeout: 10000,

  // Pagination
  defaultPageSize: 50,
  maxPageSize: 250,
} as const;
