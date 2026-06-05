export const Config = {
  // AWS
  region: process.env.AWS_REGION || 'eu-west-1',
  s3Bucket: process.env.S3_BUCKET || 'cryptools-cache',

  // Cache durations (seconds)
  cacheDuration: 60,
  newsCacheDuration: 3600,
  bscCacheDuration: 86400,

  // External APIs
  coingeckoApiBase: 'https://api.coingecko.com/api/v3',
  cryptopanicApiBase: 'https://cryptopanic.com/api/developer/v2',
  bscRpcUrl: 'https://bsc-dataseed.binance.org/',

  // Limits
  defaultPageSize: 50,
  maxPageSize: 250,
  maxStoredTokens: 200,
  requestTimeout: 10000,
} as const;
