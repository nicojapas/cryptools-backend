export const Config = {
  // AWS
  region: process.env.AWS_REGION || 'eu-west-1',
  s3Bucket: process.env.S3_BUCKET || 'cryptools-cache',

  // CryptoCompare API
  cryptocompare: {
    news: 'https://min-api.cryptocompare.com/data/v2/news/',
  },

  // Cache durations (seconds)
  cache: {
    default: 60,
    news: 3600,
  },

  // Request settings
  requestTimeout: 10000,

  // Pagination
  defaultPageSize: 50,
  maxPageSize: 250,
} as const;
