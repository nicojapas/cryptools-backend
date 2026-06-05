import { handler } from '../src/handlers/tokens';
import { APIGatewayProxyEvent, Context } from 'aws-lambda';

// Mock the cache module
jest.mock('../src/common/cache', () => ({
  getFromCache: jest.fn().mockResolvedValue(null),
  saveToCache: jest.fn().mockResolvedValue(undefined),
}));

const mockEvent = {
  queryStringParameters: null,
} as unknown as APIGatewayProxyEvent;
const mockContext = {} as Context;

const mockMarketResponse = [
  {
    id: 'bitcoin',
    symbol: 'btc',
    name: 'Bitcoin',
    image: 'https://example.com/btc.png',
    current_price: 50000,
    market_cap: 1000000000000,
    market_cap_rank: 1,
    price_change_24h: 1000,
    price_change_percentage_24h: 2.5,
    market_cap_change_24h: 20000000000,
    market_cap_change_percentage_24h: 2.1,
    circulating_supply: 19000000,
  },
  {
    id: 'ethereum',
    symbol: 'eth',
    name: 'Ethereum',
    image: 'https://example.com/eth.png',
    current_price: 3000,
    market_cap: 400000000000,
    market_cap_rank: 2,
    price_change_24h: -50,
    price_change_percentage_24h: -1.5,
    market_cap_change_24h: -5000000000,
    market_cap_change_percentage_24h: -1.2,
    circulating_supply: 120000000,
  },
];

const mockTrendingResponse = {
  coins: [
    {
      item: {
        id: 'pepe',
        name: 'Pepe',
        symbol: 'PEPE',
        score: 0,
        large: 'https://example.com/pepe.png',
      },
    },
  ],
};

describe('Tokens Handler', () => {
  const originalFetch = global.fetch;
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv, COINGECKO_API_KEY: 'test-key' };
    global.fetch = jest.fn().mockImplementation((url: string) => {
      if (url.includes('trending')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTrendingResponse),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockMarketResponse),
      });
    });
  });

  afterEach(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
  });

  it('returns 200 status code', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    expect(response?.statusCode).toBe(200);
  });

  it('returns tokens with correct structure', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.data).toHaveProperty('biggestCoins');
    expect(body.data).toHaveProperty('topGainers');
    expect(body.data).toHaveProperty('worstLosers');
    expect(body.data).toHaveProperty('trendingCoins');
    expect(body.data).toHaveProperty('banner');
    expect(body.data).toHaveProperty('sentiment');
  });

  it('returns biggestCoins with correct data', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.data.biggestCoins[0]).toMatchObject({
      name: 'Bitcoin',
      symbol: 'BTC',
      marketCapRank: 1,
    });
  });

  it('calculates sentiment based on Bitcoin', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    // Bitcoin has +2.5% change, so should be bullish
    expect(body.data.sentiment).toBe('bullish');
  });

  it('returns error when API fails', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 429,
    });

    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(response?.statusCode).toBe(500);
    expect(body.error).toContain('CoinGecko');
  });
});
