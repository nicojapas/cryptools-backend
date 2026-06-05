import { handler } from '../src/handlers/health';
import { APIGatewayProxyEvent, Context } from 'aws-lambda';

const mockEvent = {} as APIGatewayProxyEvent;
const mockContext = {} as Context;

describe('Health Handler', () => {
  it('returns 200 status code', async () => {
    const response = await handler(mockEvent, mockContext, () => {});

    expect(response?.statusCode).toBe(200);
  });

  it('returns healthy status in body', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.data.status).toBe('healthy');
    expect(body.message).toBe('Service is running');
  });

  it('includes CORS headers', async () => {
    const response = await handler(mockEvent, mockContext, () => {});

    expect(response?.headers?.['Access-Control-Allow-Origin']).toBe('*');
  });

  it('includes timestamp', async () => {
    const response = await handler(mockEvent, mockContext, () => {});
    const body = JSON.parse(response?.body || '{}');

    expect(body.timestamp).toBeDefined();
    expect(() => new Date(body.timestamp)).not.toThrow();
  });
});
