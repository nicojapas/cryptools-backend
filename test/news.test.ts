import { handler } from '../src/handlers/news';
import { APIGatewayProxyEvent, Context } from 'aws-lambda';

const mockEvent = {} as APIGatewayProxyEvent;
const mockContext = {} as Context;

const mockNewsResponse = {
  Data: [
    {
      id: '123',
      title: 'Bitcoin hits new high',
      body: 'Bitcoin reached a new all-time high today. This is great news for investors.',
      source: 'cryptonews',
      published_on: 1705320000,
      url: 'https://cryptonews.com/btc-high',
      categories: 'BTC|Trading',
      upvotes: '100',
      downvotes: '5',
      source_info: { name: 'CryptoNews' },
    },
    {
      id: '456',
      title: 'Ethereum upgrade announced',
      body: 'Major Ethereum network upgrade coming soon with improved scalability.',
      source: 'ethdaily',
      published_on: 1705316400,
      url: 'https://ethdaily.com/upgrade',
      categories: 'ETH|Technology',
      upvotes: '80',
      downvotes: '10',
      source_info: { name: 'ETH Daily' },
    },
  ],
};

describe('News Handler', () => {
  const originalFetch = global.fetch;
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv, CRYPTOCOMPARE_API_KEY: 'test-key' };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockNewsResponse),
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

  it('returns news items with correct structure', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.data.results).toHaveLength(2);
    expect(body.data.results[0]).toMatchObject({
      id: 123,
      title: 'Bitcoin hits new high',
      source: 'CryptoNews',
      url: 'https://cryptonews.com/btc-high',
      domain: 'cryptonews.com',
      currencies: ['BTC', 'Trading'],
    });
  });

  it('includes count in response', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.count).toBe(2);
  });

  it('returns error when API fails', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 429,
    });

    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(response?.statusCode).toBe(500);
    expect(body.error).toContain('CryptoCompare API error');
  });
});
